from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import tempfile
from docx import Document

from app.core.references_generator import ReferenceGenerator
from app.core.intext_citation import InTextCitationProcessor
from app.core.paper_matcher import PaperKeywordMatcher
from app.auth.helpers import get_current_active_user
from app.core.wordcount import count_words_in_docx
from app.core.category import get_document_category
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
import logging
import uuid
import json
from typing import List, Dict, Any

citations = APIRouter(prefix="/citations", tags=["Citations"])

@citations.get("/categories")
async def get_categories():
    """
    Fetch unique categories from the database.
    """
    try:
        with get_session_with_ctx_manager() as session:
            categories = session.query(Papers.category).distinct().order_by(Papers.category).all()
            # Standardize categories and remove duplicates
            standardized_categories = [category[0].lower().replace(" ", "_").strip("_") for category in categories if category[0]]
            unique_categories = sorted(list(set(standardized_categories)))

            # Ensure "healthcare_management" is unified
            unwanted_categories = {"research_topic_2", "research_topic_3", "healthcare","governance"}
            unique_categories = ["healthcare_management" if cat.startswith("healthcare_management") else cat for cat in unique_categories]
            unique_categories = [cat for cat in unique_categories if cat not in unwanted_categories]
            # Add "others" category
            if "others" not in unique_categories:
                unique_categories.append("others")

            return {"categories": unique_categories}
    except Exception as e:
        logging.error(f"Error fetching categories: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch categories: {str(e)}"}
        )


@citations.post("/char-count")
async def char_count(file: UploadFile = File(...),):
    """
    Route to count the number of characters in a given text.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await file.read())
    try:
        result = count_words_in_docx(temp_file_path)
        return result
    except Exception as e:
        return {"error": str(e)}



@citations.post("/get-category")
async def document_category(input_file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await input_file.read())

    valid_category = get_document_category(temp_file_path)
    return{"category": valid_category}
    
@citations.post("/get-citation")
async def citation_review_route(
input_file: UploadFile = File(...),
collection_name: str = Form(...)):
    """
    Example route for handling citation review process.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await input_file.read())

    try:
        collection_name = collection_name if collection_name != "others" else "healthcare_management"
        # Initialize the citation processor
        citation_processor = InTextCitationProcessor(
            style="APA",  # or any other preferred style
            collection_name=collection_name,
            threshold=0.0,
            top_k=5
        )

        # Prepare citations for review
        citation_review_data = citation_processor.prepare_citations_for_review(temp_file_path)

        # Return JSON response
        return {
            "status": "success",
            "document_id": citation_review_data["document_id"],
            "total_citations": citation_review_data["total_citations"],
            "citations": citation_review_data["citations"],
        }

    except Exception as e:
        logging.error(f"Error in citation review route: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }), 500

from pydantic import BaseModel, HttpUrl

class PaperDetails(BaseModel):
    title: str
    authors: List[str]
    year: str
    url: HttpUrl
    doi: str


class Metadata(BaseModel):
    paragraph_index: int
    sentence_index: int


class ReviewedCitation(BaseModel):
    id: str
    original_sentence: str
    paper_details: PaperDetails
    status: str
    page_number: str
    metadata: Metadata


class UpdateCitation(BaseModel):
    style: str
    reviewed_citations: List[ReviewedCitation]
@citations.post("/update-citations")
async def update_citations_route(
    updateData: UpdateCitation
):
    """
    Route for processing reviewed citations and returning formatted references.
    
    Parameters:
    - reviewed_citations (str): JSON string containing the reviewed citations
    
    Returns:
    - JSONResponse: List of formatted references
    """
    try:
        # Parse the reviewed citations JSON
        citations_data = [citation.model_dump() for citation in updateData.reviewed_citations]
        
        # Initialize the citation processor
        citation_processor = InTextCitationProcessor(
            style=updateData.style,  # This could be a parameter if needed
            collection_name="corporate_governance",
            threshold=0.5,
            top_k=3
        )

        # Get formatted references
        formatted_references = citation_processor.update_document_with_reviewed_citations(
            reviewed_citations=citations_data
        )

        # Return the formatted references
        return JSONResponse(
            content={
                "status": "success",
                "references": formatted_references
            },
            status_code=200
        )

    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON format for reviewed citations: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": "Invalid JSON format for reviewed citations"
            },
            status_code=400
        )
    except Exception as e:
        logging.error(f"Error in update citations route: {e}")
        return JSONResponse(
            content={
                "status": "error",
                "message": str(e)
            },
            status_code=500
        )

@citations.post("/extract-content")
async def extract_paper_content(file: UploadFile = File(...)):
    """
    Extracts the content from a .docx file and returns it as a joined string.
    """
    # Create a temporary file to store the uploaded document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await file.read())

    try:
        # Read the document content
        doc = Document(temp_file_path)
        # Join all paragraphs with a newline
        content = "\n".join(paragraph.text for paragraph in doc.paragraphs)
        
        return {
            "status": "success",
            "content": content,
            "message": "Content extracted successfully"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": f"Error extracting content: {str(e)}"
            }
        )

    finally:
        # Ensure the file is not in use before deletion
        try:
            Path(temp_file_path).unlink(missing_ok=True)
        except PermissionError:
            import time
            time.sleep(1)  # Small delay before retrying
            Path(temp_file_path).unlink(missing_ok=True)