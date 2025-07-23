from fastapi import APIRouter, File, UploadFile, Form, Depends
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from io import BytesIO
from pathlib import Path
import tempfile
from docx import Document

from app.core.intext_citation import AcademicCitationProcessor
from api.v1.services.temp_citation import TempCitationProcessor
from app.core.wordcount import count_words_in_docx
import logging
import os
import time

citations = APIRouter(prefix="/citations", tags=["Citations"])

@citations.get("/categories")
async def get_categories():
    """
    Fetch unique categories from the database.
    """
    try:
        categories = [
            "adult_care",
            "biology",
            "business_management",
            "cancer",
            "computer_science",
            "corporate_governance",
            "healthcare_management",
            "machine_learning",
            "marketing",
            "mathematics",
            "neuroscience",
            "physics",
            "quantum_physics",
            "others"
        ]

        return {"categories": categories}
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

    valid_category = "healthcare_management"
    return{"category": valid_category}
    
@citations.post("/get-citation")
async def citation_review_route(
    input_file: UploadFile = File(...),
    collection_name: str = Form(...),
    lightning_speed: bool = Form(True)
):
    """
    Route for handling citation review process with collection fallback.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
        temp_file_path = temp_file.name
        # Save the uploaded file to the temporary file
        temp_file.write(await input_file.read())

    try:
        # Initialize the citation processor based on the lightning_speed flag
        if lightning_speed:
            print(f"Using lightning speed mode for collection: {collection_name}")
            citation_processor = AcademicCitationProcessor(
                style="APA",
                threshold=0.0,
                top_k=5
            )
        else:
            print(f"Using standard mode for collection: {collection_name}")
            citation_processor = TempCitationProcessor(
                style="APA",
                threshold=0.0,
                top_k=5,
                additional_context=collection_name,
            )

        # Prepare citations for review
        citation_review_data = await citation_processor.prepare_citations_for_review(temp_file_path)

        response_data = {
            "status": "success",
            "document_id": citation_review_data["document_id"],
            "total_citations": citation_review_data["total_citations"],
            "citations": citation_review_data["citations"],
            "context_info": citation_review_data.get("context_info", {}),
        }

        return response_data

    except Exception as e:
        logging.error(f"Error in citation review route: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as cleanup_error:
            logging.warning(f"Could not clean up temporary file: {cleanup_error}")


# @citations.post("/get-citation-batch")
# async def citation_batch_route(
#     files: List[UploadFile] = File(...),
#     collection_name: str = Form(...),
#     max_paragraphs: int = Form(100),
#     max_concurrent: int = Form(30)
# ):
#     """
#     Batch processing route for multiple documents.
#     """
#     if len(files) > 10:
#         return JSONResponse({
#             "status": "error",
#             "message": "Maximum 10 files allowed per batch"
#         }, status_code=400)
    
#     temp_files = []
#     citation_processor = None
    
#     try:
#         start_time = time.time()
        
#         for file in files:
#             if not file.filename.endswith('.docx'):
#                 return JSONResponse({
#                     "status": "error",
#                     "message": f"File {file.filename} is not a .docx file"
#                 }, status_code=400)
        
#         collection_name = collection_name if collection_name != "others" else "healthcare_management"
        
#         citation_processor = AcademicCitationProcessor(
#             style="APA",
#             threshold=0.0,
#             top_k=5,
#             max_concurrent=max_concurrent,
#             search_providers=["semantic_scholar", "crossref", "openalex"]
#         )
        
#         batch_results = []
        
#         for file in files:
#             with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_file:
#                 temp_file_path = temp_file.name
#                 temp_files.append(temp_file_path)
#                 content = await file.read()
#                 temp_file.write(content)
            
#             try:
#                 citation_review_data = await citation_processor.prepare_citations_for_review(
#                     temp_file_path, 
#                     max_paragraphs=max_paragraphs
#                 )
                
#                 batch_results.append({
#                     "filename": file.filename,
#                     "status": "success",
#                     "document_id": citation_review_data["document_id"],
#                     "total_citations": citation_review_data["total_citations"],
#                     "citations": citation_review_data["citations"],
#                     "diagnostics": citation_review_data["diagnostics"]
#                 })
                
#             except Exception as file_error:
#                 batch_results.append({
#                     "filename": file.filename,
#                     "status": "error",
#                     "message": str(file_error)
#                 })
        
#         total_processing_time = time.time() - start_time
        
#         return {
#             "status": "success",
#             "batch_results": batch_results,
#             "batch_metrics": {
#                 "total_files": len(files),
#                 "successful_files": len([r for r in batch_results if r["status"] == "success"]),
#                 "failed_files": len([r for r in batch_results if r["status"] == "error"]),
#                 "total_processing_time_seconds": round(total_processing_time, 2)
#             }
#         }
        
#     except Exception as e:
#         logging.error(f"Error in batch citation route: {e}")
#         return JSONResponse({
#             "status": "error",
#             "message": "Batch processing error occurred"
#         }, status_code=500)
        
#     finally:
#         if citation_processor:
#             try:
#                 await citation_processor.cleanup()
#             except Exception as cleanup_error:
#                 logging.warning(f"Citation processor cleanup failed: {cleanup_error}")
        
#         for temp_file_path in temp_files:
#             try:
#                 os.unlink(temp_file_path)
#             except Exception as cleanup_error:
#                 logging.warning(f"Could not clean up temporary file: {cleanup_error}")

@citations.get("/health")
async def health_check():
    """
    Health check endpoint for citation service.
    """
    try:
        citation_processor = AcademicCitationProcessor(max_concurrent=1)
        test_result = await citation_processor.search_all_providers_async("test query", max_results=1)
        await citation_processor.cleanup()
        
        return {
            "status": "healthy",
            "services": {
                "citation_processor": "operational",
                "api_providers": len(test_result) > 0
            },
            "timestamp": time.time()
        }
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": time.time()
        }, status_code=503)
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