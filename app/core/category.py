import google.generativeai as genai
import os
import logging
from typing import Optional
from decouple import config, UndefinedValueError

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Configuration & Initialization ---
def initialize_genai_client() -> Optional[genai.GenerativeModel]:
    """Initialize and configure the Gemini API client."""
    try:
        # Try to get API key from environment or .env file
        api_key = config("GOOGLE_GEMINI_KEY")
        if not api_key:
            raise ValueError("API key is empty")
        
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-pro-latest')
    
    except UndefinedValueError:
        logger.error("GOOGLE_GEMINI_KEY not found in environment or .env file")
        return None
    except ValueError as e:
        logger.error(f"API key error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}")
        return None

# --- Valid document categories ---
VALID_CATEGORIES = [
    "biology",
    "business_management",
    "cancer",
    "computer_science",
    "corporate_governance",
    "governance",
    "healthcare_management",
    "machine_learning",
    "marketing",
    "mathematics",
    "neuroscience",
    "physics",
    "quantum_physics",
]

def get_classification_prompt() -> str:
    """Generate the classification prompt with formatted categories."""
    categories_for_prompt = "\n".join([f'- "{cat}"' for cat in VALID_CATEGORIES])
    
    return f"""
You are an AI assistant specialized in classifying document content.
The user will upload a PDF document (converted from DOCX).
Your task is to determine which of the following categories best describes the main topic of the document:

{categories_for_prompt}

Instructions:
1.  Analyze the content of the provided PDF document.
2.  Identify the single most appropriate category from the list above.
3.  Return ONLY the category string, exactly as it is spelled and cased in the list.
4.  Do not include any introductory text, explanations, markdown formatting, or any characters other than the chosen category string.

Example:
If the document is primarily about machine learning algorithms, you must return:
machine_learning

If the document is about the principles of physics, you must return:
physics
"""
from docx import Document

def read_docx_text(file_path):
    doc = Document(file_path)
    return "\n".join(para.text for para in doc.paragraphs if para.text.strip())

def get_document_category(file_path: str) -> Optional[str]:
    """
    Processes a DOCX file and determines its category using Gemini AI.
    
    Args:
        file_path: Path to a DOCX file
        
    Returns:
        A valid category string or None if processing failed
    """
    # Initialize the Gemini client
    model = initialize_genai_client()
    if not model:
        logger.error("Failed to initialize Gemini client")
        return None
    
    # Validate input file
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    if not file_path.lower().endswith(".docx"):
        logger.error(f"File is not a DOCX: {file_path}")
        return None
    
    pdf_path = None
    uploaded_file_ref = None
    
    try:
        # Convert DOCX to PDF
        texts = read_docx_text(file_path)
        if not texts:
            return None
        
        # Upload the PDF to Gemini
        # logger.info(f"Uploading PDF to Gemini: {os.path.basename(pdf_path)}")
        # uploaded_file_ref = genai.upload_file(path=pdf_path)
        # logger.info(f"File uploaded with reference: {uploaded_file_ref.name}")
        
        # Prepare the classification request
        content_parts = [get_classification_prompt() + texts]
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        generation_config = genai.types.GenerationConfig(
            max_output_tokens=50,
            temperature=0.1
        )
        
        # Send the request to Gemini
        logger.info("Requesting document classification from Gemini")
        response = model.generate_content(
            content_parts,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
        # Extract the category from the response
        response_text = ""
        if response.parts:
            response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text'):
            response_text = response.text
        else:
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                logger.error(f"Request blocked: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}")
            else:
                logger.error("No text in response and no block reason provided")
            return None
        
        # Validate the category
        extracted_category = response_text.strip()
        logger.info(f"Received category: '{extracted_category}'")
        
        if extracted_category in VALID_CATEGORIES:
            logger.info(f"Valid category identified: {extracted_category}")
            return extracted_category
        else:
            logger.error(f"Invalid category returned: '{extracted_category}'")
            return None
    
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        return None
    

def main():
    """Main function to demonstrate usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Document Category Classifier")
    parser.add_argument("docx_file", help="Path to DOCX file for classification")
    
    args = parser.parse_args()
    
    category = get_document_category(args.docx_file)
    if category:
        print(f"Document Category: {category}")
    else:
        print("Document classification failed")

if __name__ == "__main__":
    main()