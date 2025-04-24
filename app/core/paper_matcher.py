import os
from docx import Document
from sqlalchemy.orm import Session
from datapipeline.core.database import get_session_with_ctx_manager
from app.core.extract_keywords import ExtractKeywords
from datapipeline.models.papers import Papers
from datapipeline.main import PapersPipeline
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import logging


class PaperKeywordMatcher:
    def __init__(self):
        self.keyword_extractor = ExtractKeywords()
        self.pipeline = PapersPipeline(
            mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
            mongo_db_name=MONGO_DB_NAME
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.category_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert in academic paper categorization. Your task is to analyze the content of a paper and suggest the most appropriate category for it. The category should be specific and relevant to the paper's content."
            ),
            ("human", "Here is the paper content:\n\n{content}\n\nPlease suggest the most appropriate category for this paper. Return only the category name, nothing else.")
        ])
        self.category_validation_prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "You are an expert in academic paper categorization. Your task is to validate if a given category is appropriate for a paper's content. Return 'true' if the category is appropriate, 'false' otherwise."
            ),
            ("human", "Paper content:\n\n{content}\n\nCategory to validate: {category}\n\nIs this category appropriate for the paper? Return only 'true' or 'false'.")
        ])

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

    def generate_category_from_content(self, content: str) -> str:
        """
        Generates an appropriate category for the paper content using LLM.
        """
        try:
            chain = self.category_prompt | self.llm
            response = chain.invoke({"content": content})
            
            # Extract the category from the response
            if isinstance(response, dict) and "content" in response:
                category = response["content"].strip()
            else:
                category = str(response).strip()
            
            return category
        except Exception as e:
            logging.error(f"Error generating category: {e}")
            return ""

    def validate_category(self, content: str, category: str) -> bool:
        """
        Validates if a category is appropriate for the paper content using LLM.
        """
        try:
            chain = self.category_validation_prompt | self.llm
            response = chain.invoke({"content": content, "category": category})
            
            # Extract the validation result
            if isinstance(response, dict) and "content" in response:
                result = response["content"].strip().lower()
            else:
                result = str(response).strip().lower()
            
            return result == "true"
        except Exception as e:
            logging.error(f"Error validating category: {e}")
            return False

    def generate_query_from_content(self, content: str) -> str:
        """
        Generates a search query from the document content using the first few sentences.
        """
        # Split content into sentences and take the first few
        sentences = content.split('.')
        first_sentences = '.'.join(sentences[:3])  # Take first 3 sentences
        
        # Extract keywords from these sentences
        keywords = self.keyword_extractor.extract_keywords(first_sentences)
        
        # Combine keywords into a query
        if keywords:
            return ' '.join(keywords[:5])  # Use top 5 keywords
        return ""

    def get_available_categories(self) -> list:
        """
        Fetches all available categories from the database.
        """
        with get_session_with_ctx_manager() as session:
            categories = session.query(Papers.category).distinct().all()
            return [category[0] for category in categories if category[0]]

    def find_matching_papers_with_retry(self, file_path: str, initial_category: str) -> tuple:
        """
        Tries to find matching papers by:
        1. First trying the initial category
        2. If no matches, generating a query and trying other categories
        3. If still no matches, generating a new category and processing papers
        4. If still no matches, validating the generated category with LLM
        
        Returns:
        - tuple: (matching_titles, category_used)
        """
        # First try with initial category
        matching_titles = self.match_keywords(file_path, initial_category)
        if matching_titles:
            return matching_titles, initial_category

        # If no matches, read content and generate query
        content = self.read_file_content(file_path)
        if not content:
            return [], initial_category

        # Try other categories with the generated query
        available_categories = self.get_available_categories()
        for category in available_categories:
            if category != initial_category:
                # Process new papers for this category
                self.pipeline.process_papers(
                    query=self.generate_query_from_content(content),
                    category=category,
                    batch_size=10,
                    sources=["elsevier", "springer"]
                )
                
                # Try matching again
                matching_titles = self.match_keywords(file_path, category)
                if matching_titles:
                    return matching_titles, category

        # If still no matches, generate a new category
        generated_category = self.generate_category_from_content(content)
        if generated_category:
            # Validate the generated category
            if self.validate_category(content, generated_category):
                # Process papers with the new category
                self.pipeline.process_papers(
                    query=self.generate_query_from_content(content),
                    category=generated_category,
                    batch_size=10,
                    sources=["arxiv", "elsevier", "springer"]
                )
                
                # Try matching with the new category
                matching_titles = self.match_keywords(file_path, generated_category)
                if matching_titles:
                    return matching_titles, generated_category

        return [], initial_category

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
                            keyword.strip().strip("\"'").lower() for keyword in paper.keywords.split(",")
                        )

                    # Compare with extracted keywords
                    extracted_keywords_set = {
                        keyword.strip().strip("\"'").strip("*").lower() for keyword in extracted_keywords
                    }

                    if db_keywords.intersection({kw.lower() for kw in extracted_keywords_set}):
                        matching_titles.append(paper.title)

            return matching_titles