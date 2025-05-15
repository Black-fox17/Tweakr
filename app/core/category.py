import google.generativeai as genai
import os
from decouple import config
import subprocess
import tempfile

# --- Configuration & Initialization ---
try:
    api_key = config("GOOGLE_GEMINI_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment or .env file.")
    genai.configure(api_key=api_key)
except Exception as e:
    print(f"Error during configuration: {e}")
    exit()

try:
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
except Exception as e:
    print(f"Error initializing GenerativeModel. Check model name and API key validity. Error: {e}")
    exit()

# --- List of valid categories ---
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

categories_for_prompt = "\n".join([f'- "{cat}"' for cat in VALID_CATEGORIES])

classification_prompt = f"""
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

def convert_to_pdf(docx_file):
    """Converts a DOCX file to PDF using LibreOffice."""
    temp_dir = tempfile.gettempdir()
    file_name = os.path.splitext(os.path.basename(docx_file))[0]
    pdf_file = os.path.join(temp_dir, f"{file_name}.pdf")

    try:
        # Ensure LibreOffice is correctly installed and in the PATH
        command = [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            temp_dir,
            docx_file,
        ]
        print(f"Executing command: {' '.join(command)}") # Debugging
        subprocess.run(command, check=True, capture_output=True, text=True)

        return pdf_file  # Return the path to the generated PDF
    except subprocess.CalledProcessError as e:
        print(f"Error during LibreOffice conversion: {e.stderr}")
        return None
    except FileNotFoundError:
        print("Error: LibreOffice not found.  Ensure it's installed and in your PATH.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during conversion: {e}")
        return None
    
def get_document_category(file_path: str) -> str | None:
    """
    Converts a DOCX file to PDF, uploads it to Gemini and determines its category.

    Args:
        file_path: Path to a single DOCX file.

    Returns:
        A string containing the category, or None if an error occurs or
        the category cannot be determined or is invalid.
    """
    uploaded_file_ref = None # Initialize to ensure it's defined for the finally block
    pdf_path = None
    
    try:
        if not os.path.exists(file_path):
            print(f"Error: File not found at '{file_path}'.")
            return None

        if not file_path.lower().endswith(".docx"):
            print(f"Error: File '{os.path.basename(file_path)}' is not a DOCX file.")
            return None
        
        # Create a temporary file for the PDF output
        temp_dir = tempfile.gettempdir()
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        pdf_path = os.path.join(temp_dir, f"{file_name}.pdf")
        
        print(f"Converting DOCX to PDF: {os.path.basename(file_path)} -> {os.path.basename(pdf_path)}...")
        # Convert the DOCX to PDF
        pdf_path = convert_to_pdf(file_path, pdf_path)
        
        if not os.path.exists(pdf_path):
            print(f"Error: PDF conversion failed. No file was created at '{pdf_path}'.")
            return None
        
        print(f"Uploading PDF: {os.path.basename(pdf_path)}...")
        # Upload the PDF file
        uploaded_file_ref = genai.upload_file(path=pdf_path)
        print(f"File uploaded successfully: {uploaded_file_ref.name}")

        content_parts = [classification_prompt, uploaded_file_ref]

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

        print("Requesting document category from model...")
        response = model.generate_content(
            content_parts,
            generation_config=generation_config,
            safety_settings=safety_settings
        )

        response_text = ""
        if response.parts:
            response_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        elif hasattr(response, 'text'): # Check if response itself has text (for non-multi-part)
             response_text = response.text
        else:
            # Check for blocking due to safety or other reasons
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                print(f"Error: Request blocked. Reason: {response.prompt_feedback.block_reason_message or response.prompt_feedback.block_reason}")
            else:
                print("Error: No text found in the model's response and no explicit block reason.")
            return None

        extracted_category = response_text.strip()
        print(f"Model response: '{extracted_category}'")

        if extracted_category in VALID_CATEGORIES:
            print(f"Valid category identified: {extracted_category}")
            return extracted_category
        else:
            print(f"Error: Model returned an invalid or unexpected category: '{extracted_category}'.")
            print(f"Please ensure the model returns one of: {', '.join(VALID_CATEGORIES)}")
            return None

    except Exception as e:
        print(f"An error occurred during processing '{os.path.basename(file_path)}': {e}")
        return None
    finally:
        # Clean up the temporary PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Deleted temporary PDF file: {pdf_path}")
            except Exception as e:
                print(f"Error deleting temporary PDF file: {e}")
                
        # Clean up the uploaded file reference
        if uploaded_file_ref and hasattr(uploaded_file_ref, 'name'):
            try:
                print(f"Attempting to delete uploaded file: {uploaded_file_ref.name}")
                genai.delete_file(uploaded_file_ref.name)
                print(f"Successfully deleted file: {uploaded_file_ref.name}")
            except Exception as del_e:
                print(f"Error deleting uploaded file '{uploaded_file_ref.name}' during final cleanup: {del_e}")
