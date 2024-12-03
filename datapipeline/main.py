# import os
# from sqlalchemy import create_engine, sessionmaker
# from sqlalchemy.orm import Session
# from sqlalchemy.exc import IntegrityError
# from datetime import datetime
# from pymongo import MongoClient
# from langchain_community.vectorstores import MongoDBAtlasVectorSearch
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain.docstore.document import Document


# from datapipeline.core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
# from datapipeline.core.database import Base
# from datapipeline.models.papers import Papers
# from datapipeline.core.download_arxiv_paper import ArxivPaperDownloader
# from datapipeline.core.extract_contents_arxiv_paper import ArxivPaperFetcher
# from datapipeline.core.mongo_client import MongoDBVectorStoreManager



# class PapersPipeline:
#     def __init__(self, db_url: str, mongo_uri: str, mongo_db_name: str):
#         # Setup SQLAlchemy database connection
#         self.engine = create_engine(db_url)
#         self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
#         Base.metadata.create_all(bind=self.engine)

#         # Setup MongoDB manager
#         self.mongo_manager = MongoDBVectorStoreManager(connection_string=mongo_uri, db_name=mongo_db_name)

#     def save_paper_metadata(self, session: Session, paper_data: dict):
#         paper = Papers(
#             title=paper_data['title'],
#             category=paper_data['category'],
#             pub_date=paper_data['published_date'],
#             collection_name=paper_data['category'],
#             is_processed=paper_data.get('is_processed', False)
#         )
#         try:
#             session.add(paper)
#             session.commit()
#         except IntegrityError:
#             session.rollback()
#             print(f"Paper with title '{paper.title}' already exists in the database.")

#     def process_papers(self, query: str, category: str, max_results: int = 10, download_dir: str = './store'):
#         downloader = ArxivPaperDownloader(query=query, max_results=max_results, download_dir=download_dir)
#         downloaded_papers = downloader.download_papers()

#         with self.SessionLocal() as session:
#             for paper in downloaded_papers:
#                 print(f"Processing paper: {paper['title']}")

#                 # Step 2: Fetch paper content
#                 fetcher = ArxivPaperFetcher(title_query=paper['title'])
#                 fetcher.fetch_paper()
#                 content = fetcher.get_content()

#                 if content:
#                     # Store content in MongoDB vector store
#                     document = Document(
#                         page_content=content,
#                         metadata={
#                             "title": fetcher.get_title(),
#                             "authors": fetcher.get_authors(),
#                             "published_date": fetcher.get_published_date(),
#                             "summary": fetcher.get_summary()
#                         }
#                     )
#                     self.mongo_manager.store_document(collection_name=category, document=document)
#                     print(f"Document stored in MongoDB collection '{category}'.")

#                     # Step 3: Save paper metadata to SQL database
#                     paper_data = {
#                         "title": fetcher.get_title(),
#                         "category": category,
#                         "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
#                         "keywords": None,  # Add logic to extract keywords if available
#                         "collection_name": category,
#                         "is_processed": True
#                     }
#                     self.save_paper_metadata(session, paper_data)
#                 else:
#                     print(f"No content found for paper: {paper['title']}")

# # Example Usage
# if __name__ == "__main__":
#     DB_URL = "sqlite:///papers.db"  # Change to your database URL

#     pipeline = PapersPipeline(db_url=DB_URL, mongo_uri=MONGODB_ATLAS_CLUSTER_URI, mongo_db_name=MONGO_DB_NAME)
#     pipeline.process_papers(query="quantum", category="quantum_physics", max_results=10, download_dir='./store')


from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from langchain.docstore.document import Document

from core.constants import MONGO_DB_NAME, MONGODB_ATLAS_CLUSTER_URI
from models.papers import Papers
from core.download_arxiv_paper import ArxivPaperDownloader
from core.extract_contents_arxiv_paper import ArxivPaperFetcher
from core.mongo_client import MongoDBVectorStoreManager
from core.database import get_session


class PapersPipeline:
    def __init__(self, mongo_uri: str, mongo_db_name: str):
        # Setup MongoDB manager
        self.mongo_manager = MongoDBVectorStoreManager(connection_string=mongo_uri, db_name=mongo_db_name)

    def save_paper_metadata(self, session: Session, paper_data: dict):
        """
        Save paper metadata to the database.
        """
        paper = Papers(
            title=paper_data['title'],
            category=paper_data['category'],
            pub_date=paper_data['published_date'],
            collection_name=paper_data['category'],
            is_processed=paper_data.get('is_processed', False)
        )
        try:
            session.add(paper)
            session.commit()
        except IntegrityError:
            session.rollback()
            print(f"Paper with title '{paper.title}' already exists in the database.")

    def process_papers(self, query: str, category: str, max_results: int = 10, download_dir: str = './store'):
        """
        Process papers by downloading, fetching their contents, and storing them in the database and MongoDB.
        """
        downloader = ArxivPaperDownloader(query=query, max_results=max_results, download_dir=download_dir)
        downloaded_papers = downloader.download_papers()

        for paper in downloaded_papers:
            print(f"Processing paper: {paper['title']}")

            # Fetch paper content
            fetcher = ArxivPaperFetcher(title_query=paper['title'])
            fetcher.fetch_paper()
            content = fetcher.get_content()

            if content:
                # Store content in MongoDB vector store
                document = Document(
                    page_content=content,
                    metadata={
                        "title": fetcher.get_title(),
                        "authors": fetcher.get_authors(),
                        "published_date": fetcher.get_published_date(),
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
                    "keywords": None,  # Add logic to extract keywords if available
                    "collection_name": category,
                    "is_processed": True
                }

                # Use get_session to save paper metadata
                with get_session() as session:
                    self.save_paper_metadata(session, paper_data)
            else:
                print(f"No content found for paper: {paper['title']}")

# Example Usage
if __name__ == "__main__":
    pipeline = PapersPipeline(mongo_uri=MONGODB_ATLAS_CLUSTER_URI, mongo_db_name=MONGO_DB_NAME)
    pipeline.process_papers(query="quantum", category="quantum_physics", max_results=10, download_dir='./store')
