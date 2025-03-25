from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import tempfile

from app.core.references_generator import ReferenceGenerator
from app.core.intext_citation import InTextCitationProcessor
from app.core.paper_matcher import PaperKeywordMatcher
from app.auth.helpers import get_current_active_user
from app.core.wordcount import count_words_in_docx
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
