import os
from docx import Document
from sqlalchemy.orm import Session
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.core.extract_keywords import ExtractKeywords
from datapipeline.models.papers import Papers
from app.core.references_generator import ReferenceGenerator
from app.core.intext_citation import InTextCitationProcessor

class PaperKeywordMatcher:
    def __init__(self):
        self.keyword_extractor = ExtractKeywords()

    def read_file_content(self, file_path: str) -> str:
        """
        Reads the content of a file based on its type.
        """
        # Check if the file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist.")
            return ""

        # Detect file type and process accordingly
        file_extension = os.path.splitext(file_path)[1].lower()
        try:
            if file_extension == ".txt":
                # Handle plain text files
                with open(file_path, 'r', encoding='utf-8') as file:
                    return file.read()
            elif file_extension == ".docx":
                # Handle .docx files using python-docx
                doc = Document(file_path)
                # Join all paragraphs with a newline
                return "\n".join(paragraph.text for paragraph in doc.paragraphs)
            else:
                print(f"Unsupported file type: {file_extension}")
                return ""
        except Exception as e:
            print(f"Error reading file '{file_path}': {e}")
            return ""


    def fetch_papers_by_category(self, session: Session, category: str) -> list:
        """
        Fetches papers from the database for the given category.
        """
        return session.query(Papers).filter(Papers.category == category).all()


    def match_keywords(self, file_path: str, category: str) -> list:
        """
        Matches keywords from a file with those in the database for a specific category.
        """
        # Step 1: Read content from the file
        file_content = self.read_file_content(file_path)
        if not file_content:
            print("File content is empty. Aborting.")
            return []

        # Step 2: Extract keywords from the file
        extracted_keywords = self.keyword_extractor.extract_keywords(file_content)
        if not extracted_keywords:
            print("No keywords extracted from the file. Aborting.")
            return []

        print(f"Extracted Keywords: {extracted_keywords}")

        # Step 3: Fetch papers from the database by category
        with get_session_with_ctx_manager() as session:
            papers = self.fetch_papers_by_category(session, category)
            if not papers:
                print(f"No papers found for category '{category}'.")
                return []

            # Step 4: Match keywords
            matching_titles = []
            for paper in papers:
                if paper.keywords:  # Ensure the paper has keywords
                    # Convert the stored keywords string into a set of individual keywords
                    db_keywords = set(
                        keyword.strip().strip("\"").strip("'")
                        for keyword in paper.keywords.split(",")
                    )

                    # Compare with extracted keywords
                    extracted_keywords_set = set(extracted_keywords)
                    if db_keywords.intersection(extracted_keywords_set):
                        matching_titles.append(paper.title)

            return matching_titles


if __name__ == "__main__":
    matcher = PaperKeywordMatcher()
    file_path = "/Users/naija/Documents/gigs/tweakr/tweakr-mvp/test_docs/testdoc.docx"
    category = "quantum_physics"
    matching_titles = matcher.match_keywords(file_path, category)

    if matching_titles:
        print("Matching Papers:")
        for title in matching_titles:
            print(f"- {title}")

        reference_generator = ReferenceGenerator(style="APA")
        references = reference_generator.generate_references(matching_titles, category)

        print("\nReferences:")
        for reference in references:
            print(f"- {reference}")
        try:
            intext_citation = InTextCitationProcessor(style="APA")
            modified_file_path = intext_citation.process_draft(file_path, matching_titles, category)
            print(f"Modified draft saved to: {modified_file_path}")
        except Exception as e:
            print(f"Error processing draft: {e}")
    else:
        print("No matching papers found.")
