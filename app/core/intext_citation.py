import os
from docx import Document
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from app.core.references_generator import ReferenceGenerator

class InTextCitationProcessor:
    def __init__(self, style="APA"):
        """
        Initializes the processor with a specified reference style.

        Parameters:
        - style (str): The citation style to use (e.g., APA, MLA, Chicago).
        """
        self.style = style
        self.reference_generator = ReferenceGenerator(style)

    def read_file_content(self, file_path: str) -> str:
        """
        Reads the content of a file based on its type.

        Parameters:
        - file_path (str): Path to the file to read.

        Returns:
        - str: The content of the file as a string.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Error: File '{file_path}' does not exist.")

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".txt":
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif file_extension == ".docx":
            doc = Document(file_path)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

    def fetch_papers_by_titles(self, session: Session, titles: List[str], category: str) -> dict:
        """
        Fetches papers from the database by their titles and category.

        Parameters:
        - session (Session): The database session.
        - titles (List[str]): List of paper titles to fetch.
        - category (str): The category of the papers.

        Returns:
        - dict: A dictionary mapping titles to their respective Papers objects.
        """
        papers = session.query(Papers).filter(Papers.title.in_(titles), Papers.category == category).all()
        return {paper.title: paper for paper in papers}

    def match_keywords_and_cite(self, file_content: str, papers: dict) -> str:
        """
        Matches keywords in the draft content and inserts in-text citations.

        Parameters:
        - file_content (str): The content of the draft.
        - papers (dict): A dictionary of Papers objects indexed by title.

        Returns:
        - str: The modified content with in-text citations.
        """
        sentences = file_content.split(". ")  # Basic sentence split
        modified_sentences = []

        for sentence in sentences:
            citation_added = False
            for title, paper in papers.items():
                if paper.keywords:
                    db_keywords = set(
                        keyword.strip().strip("\"").strip("'")
                        for keyword in paper.keywords.split(",")
                    )

                    # Check if any keyword matches the sentence
                    if any(keyword.lower() in sentence.lower() for keyword in db_keywords):
                        authors = self.reference_generator.parse_authors(paper.authors)
                        pub_year = paper.pub_date.year if isinstance(paper.pub_date, datetime) else "n.d."

                        if self.style == "APA":
                            citation = f" ({', '.join(authors)}, {pub_year})"
                        elif self.style == "MLA":
                            citation = f" ({authors[0]} et al., {pub_year})" if authors else f" ({pub_year})"
                        elif self.style == "Chicago":
                            citation = f" ({', '.join(authors)}, {pub_year})"
                        else:
                            citation = ""  # Unsupported style

                        sentence += citation
                        citation_added = True
                        break  # Avoid duplicate citations in the same sentence

            modified_sentences.append(sentence)

        return ". ".join(modified_sentences)

    def save_modified_draft(self, file_path: str, modified_content: str) -> str:
        """
        Saves the modified content to a new file.

        Parameters:
        - file_path (str): The original file path.
        - modified_content (str): The content with in-text citations.

        Returns:
        - str: The path to the saved file.
        """
        base, ext = os.path.splitext(file_path)
        new_file_path = f"{base}_with_citations{ext}"

        if ext == ".txt":
            with open(new_file_path, "w", encoding="utf-8") as file:
                file.write(modified_content)
        elif ext == ".docx":
            doc = Document()
            for paragraph in modified_content.split("\n"):
                doc.add_paragraph(paragraph)
            doc.save(new_file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        return new_file_path

    def process_draft(self, file_path: str, matching_titles: List[str], category: str) -> str:
        """
        Main function to process the draft and insert in-text citations.

        Parameters:
        - file_path (str): Path to the draft file.
        - matching_titles (List[str]): List of matching paper titles.
        - category (str): Category of the papers.

        Returns:
        - str: Path to the modified draft file.
        """
        file_content = self.read_file_content(file_path)
        with get_session_with_ctx_manager() as session:
            papers = self.fetch_papers_by_titles(session, matching_titles, category)
        
        modified_content = self.match_keywords_and_cite(file_content, papers)
        modified_file_path = self.save_modified_draft(file_path, modified_content)

        return modified_file_path
