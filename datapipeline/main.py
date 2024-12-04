from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from langchain.docstore.document import Document
from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    HarmBlockThreshold,
    HarmCategory,
)
from langchain_core.prompts import ChatPromptTemplate

from datapipeline.core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
from datapipeline.models.papers import Papers
from datapipeline.core.download_arxiv_paper import ArxivPaperDownloader
from datapipeline.core.extract_contents_arxiv_paper import ArxivPaperFetcher
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.core.retry_with_backoff import retry_with_backoff


class PapersPipeline:
    def __init__(self, mongo_uri: str, mongo_db_name: str):
        # Setup MongoDB manager
        self.mongo_manager = MongoDBVectorStoreManager(connection_string=mongo_uri, db_name=mongo_db_name)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            safety_settings={
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
        )

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an advanced AI assistant specialized in natural language processing. Your task is to extract all meaningful keywords from the given academic text. Focus on identifying key concepts, topics, and important terms.",
                ),
                ("human", "Here is the academic text:\n\n{text}\n\nPlease provide a list of keywords extracted from this text."),
            ]
        )



    def extract_keywords(self, content: str) -> list:
        """
        Extract keywords from the paper content using ChatGoogleGenerativeAI.
        """
        try:
            def fetch_response():
                chain = self.prompt | self.llm
                return chain.invoke({"text": content})

            # Call the fetch_response function with retry logic
            response = retry_with_backoff(fetch_response, max_retries=1, initial_delay=3)
            print("Raw Response: ", response)

            # Check if the response is a dictionary and extract the "content" field
            if isinstance(response, dict) and "content" in response:
                content_text = response["content"]
            else:
                # Attempt to parse the response as a string
                response_str = str(response)
                if "content=" in response_str:
                    content_start = response_str.find("content='") + len("content='")
                    content_end = response_str.find("'", content_start)
                    content_text = response_str[content_start:content_end]
                else:
                    raise ValueError("Could not extract 'content' from response.")

            # Clean and process the content text
            content_text = content_text.replace("\\n", "\n")
            keywords = []

            for line in content_text.splitlines():
                # Strip leading '*' or '**', as well as any extra spaces
                cleaned_keyword = line.lstrip("* ").lstrip("**").strip()
                if cleaned_keyword and not any(
                    unwanted in cleaned_keyword for unwanted in ["additional_kwargs", "response_metadata", "usage_metadata"]
                ):
                    keywords.append(cleaned_keyword)

            print("Extracted Keywords: ", keywords)
            return keywords

        except Exception as e:
            print(f"Error extracting keywords: {e}")
            return []



    def save_paper_metadata(self, session: Session, paper_data: dict):
        """
        Save or update paper metadata in the database.
        If the paper exists, skip saving or update the keywords if necessary.
        """
        try:
            # Check if the paper already exists
            existing_paper = session.query(Papers).filter_by(title=paper_data['title']).first()

            if existing_paper:
                print(f"Paper '{existing_paper.title}' already exists in the database.")
                # Update keywords if they are empty or None
                if not existing_paper.keywords and paper_data.get('keywords'):
                    existing_paper.keywords = paper_data['keywords']
                    session.commit()
                    print(f"Updated keywords for paper: {existing_paper.title}")
                return  # Skip saving the paper as it already exists
            else:
                # Add new paper record
                paper = Papers(
                    title=paper_data['title'],
                    category=paper_data['category'],
                    pub_date=paper_data['published_date'],
                    collection_name=paper_data['collection_name'],
                    keywords=paper_data.get('keywords', []),
                    is_processed=paper_data.get('is_processed', False)
                )
                session.add(paper)
                session.commit()
                print(f"Added new paper: {paper.title}")
        except IntegrityError:
            session.rollback()
            print(f"Failed to save paper: {paper_data['title']} due to an integrity error.")
        except Exception as e:
            session.rollback()
            print(f"An error occurred while saving paper metadata: {e}")

    def process_papers(self, query: str, category: str, max_results: int = 20, download_dir: str = './store'):
        """
        Process papers by downloading, fetching their contents, and storing them in the database and MongoDB.
        """
        downloader = ArxivPaperDownloader(query=query, max_results=max_results, download_dir=download_dir)
        downloaded_papers = downloader.download_papers()

        for paper in downloaded_papers:
            print(f"Processing paper: {paper['title']}")

            # Check if the paper title already exists in MongoDB
            if self.mongo_manager.document_exists(collection_name=category, title=paper['title']):
                print(f"Paper '{paper['title']}' already exists in MongoDB. Skipping.")
                continue

            # Fetch paper content
            fetcher = ArxivPaperFetcher(title_query=paper['title'])
            fetcher.fetch_paper()
            content = fetcher.get_content()

            if content:
                # Extract keywords
                keywords = self.extract_keywords(content)
                # print("Keywords to store: ", keywords)

                # Store content in MongoDB vector store
                document = Document(
                    page_content=content,
                    metadata={
                        "title": fetcher.get_title(),
                        "authors": fetcher.get_authors(),
                        "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                        "keywords": keywords,
                        "summary": fetcher.get_summary()
                    }
                )
                self.mongo_manager.store_document(collection_name=category, document=document)
                print(f"Document stored in MongoDB collection '{category}'.")

                # Save paper metadata to SQL database
                paper_data = {
                    "title": fetcher.get_title(),
                    "category": category,
                    "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                    "keywords": keywords,
                    "collection_name": category,
                    "is_processed": True
                }

                with get_session_with_ctx_manager() as session:
                    self.save_paper_metadata(session, paper_data)
            else:
                print(f"No content found for paper: {paper['title']}")

# Example Usage
if __name__ == "__main__":
    pipeline = PapersPipeline(mongo_uri=MONGODB_ATLAS_CLUSTER_URI, mongo_db_name=MONGO_DB_NAME)
    pipeline.process_papers(query="quantum", category="quantum_physics", max_results=20, download_dir='./store')
