from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import tempfile

from app.core.references_generator import ReferenceGenerator
from app.core.intext_citation import InTextCitationProcessor
from app.core.paper_matcher import PaperKeywordMatcher
from app.auth.helpers import get_current_active_user
from app.core.wordcount import count_words_in_docx
import logging
import uuid
import json
from typing import List, Dict, Any

router = APIRouter()

@router.post("/char-count")
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


@router.post("/process-paper/")
async def process_paper(
    file: UploadFile = File(...),
    style: str = Form(...),
    category: str = Form(...),
):
    """
    Route to process an academic paper, generate references and in-text citations
    based on the provided citation style and category.
    """
    # Create a temporary file to store the uploaded document
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await file.read())

    try:
        # Initialize PaperKeywordMatcher
        matcher = PaperKeywordMatcher()

        # Get matching titles based on the document content and category
        matching_titles = matcher.match_keywords(temp_file_path, category)
        if matching_titles:
            # Generate references
            reference_generator = ReferenceGenerator(style=style)
            references = reference_generator.generate_references(matching_titles, category)

            print(references)

            # Process in-text citations and save the modified document
            intext_citation_processor = InTextCitationProcessor(style=style, collection_name=category)
            output_file_path = temp_file_path.replace(".docx", "_with_citations.docx")
            modified_file_path = intext_citation_processor.process_sentences(temp_file_path, output_file_path)

            # Return the modified document as a response
            return FileResponse(
                modified_file_path,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                filename="modified_paper.docx"
            )
        else:
            return {"message": "No matching papers found."}

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Ensure the file is not in use before deletion
        try:
            Path(temp_file_path).unlink(missing_ok=True)
        except PermissionError:
            import time
            time.sleep(1)  # Small delay before retrying
            Path(temp_file_path).unlink(missing_ok=True)

@router.post("/get-citation")
async def citation_review_route(input_file: UploadFile = File(...)):
    """
    Example route for handling citation review process.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await input_file.read())

    try:
        # Initialize the citation processor
        citation_processor = InTextCitationProcessor(
            style="APA",  # or any other preferred style
            collection_name="corporate_governance",
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
            "citations": citation_review_data["citations"]
        }

    except Exception as e:
        logging.error(f"Error in citation review route: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }), 500

async def update_citations_route(document_id, reviewed_citations):
    """
    Example route for updating document with reviewed citations.
    """
    try:
        # Initialize the citation processor
        citation_processor = InTextCitationProcessor(
            style="APA",  # or any other preferred style
            collection_name="academic_papers",
            threshold=0.5,
            top_k=3
        )

        # Provide paths for input and output documents
        input_file = f"path/to/documents/{document_id}_input.docx"
        output_file = f"path/to/documents/{document_id}_output.docx"

        # Update the document with reviewed citations
        updated_file_path = citation_processor.update_document_with_reviewed_citations(
            input_path=input_file,
            output_path=output_file,
            reviewed_citations=reviewed_citations
        )

        return JSONResponse({
            "status": "success",
            "message": "Citations updated successfully",
            "output_file": updated_file_path
        }), 200

    except Exception as e:
        logging.error(f"Error in update citations route: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }), 500