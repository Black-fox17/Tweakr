from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import tempfile

from app.core.references_generator import ReferenceGenerator
from app.core.intext_citation import InTextCitationProcessor
from app.core.paper_matcher import PaperKeywordMatcher
from app.auth.helpers import get_current_active_user

router = APIRouter()

@router.post("/process-paper/")
async def process_paper(
    file: UploadFile = File(...),
    style: str = Form(...),
    category: str = Form(...),
    current_user: User = Depends(get_current_active_user)

):
    """
    Route to process an academic paper, generate references and in-text citations
    based on the provided citation style and category.
    """
    # Create a temporary file to store the uploaded document
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    temp_file_path = temp_file.name

    # Save the uploaded file to the temporary file
    try:
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())
        
        # Initialize PaperKeywordMatcher
        matcher = PaperKeywordMatcher()

        # Get matching titles based on the document content and category
        matching_titles = matcher.match_keywords(temp_file_path, category)

        if matching_titles:
            # Generate references
            reference_generator = ReferenceGenerator(style=style)
            references = reference_generator.generate_references(matching_titles, category)

            # Process in-text citations and save the modified document
            intext_citation_processor = InTextCitationProcessor(style=style, collection_name=category)
            output_file_path = temp_file_path.replace(".docx", "_with_citations.docx")
            modified_file_path = intext_citation_processor.process_sentences(temp_file_path, output_file_path)

            # Return the modified document as a response
            return FileResponse(modified_file_path, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename="modified_paper.docx")
        
        else:
            return {"message": "No matching papers found."}

    except Exception as e:
        return {"error": str(e)}

    finally:
        # Clean up the temporary file
        Path(temp_file_path).unlink(missing_ok=True)
