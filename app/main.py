from sqlalchemy.orm import Session
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.core.extract_keywords import ExtractKeywords
from datapipeline.models.papers import Papers

class PaperKeywordMatcher:
    def __init__(self):
        self.keyword_extractor = ExtractKeywords()

    def read_file_content(self, file_path: str) -> str:
        """
        Reads the content of a file.
        """
        try:
            with open(file_path, 'r') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
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
                    db_keywords = set(paper.keywords)
                    extracted_keywords_set = set(extracted_keywords)
                    if db_keywords.intersection(extracted_keywords_set):
                        matching_titles.append(paper.title)

            return matching_titles


if __name__ == "__main__":
    matcher = PaperKeywordMatcher()
    file_path = input("Enter the path to the file: ")
    category = input("Enter the category to search: ")
    matching_titles = matcher.match_keywords(file_path, category)

    if matching_titles:
        print("Matching Papers:")
        for title in matching_titles:
            print(f"- {title}")
    else:
        print("No matching papers found.")
