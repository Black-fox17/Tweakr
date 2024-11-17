import glob

from process_document import process_document

def main_pipeline(directory, category):
    # Process all PDF files in a directory
    pdf_files = glob.glob(f"{directory}/*.pdf")
    for file_path in pdf_files:
        try:
            s3_location = process_document(file_path, category)
            print(f"Document stored at: {s3_location}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

if __name__ == "__main__":
    main_pipeline(directory="/path/to/pdf/files", category="Physics")
