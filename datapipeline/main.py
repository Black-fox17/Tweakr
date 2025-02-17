import os
from typing import Optional, List
from datetime import datetime
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
from datapipeline.core.elsevier_paper_fetcher import ElsevierPaperFetcher
from datapipeline.core.springer_paper_fetcher import SpringerPaperFetcher
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


    def clean_download_directory(self, download_dir: str):
        """
        Empties the specified directory to prepare it for the next batch of downloads.

        Parameters:
        - download_dir (str): The directory to clean.
        """
        if os.path.exists(download_dir):
            for filename in os.listdir(download_dir):
                file_path = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            os.makedirs(download_dir)


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
                

                if not existing_paper.url and paper_data.get('url'):
                    existing_paper.url = paper_data['url']
                    session.commit()
                    print(f"Updated url for paper: {existing_paper.title}")

                # Update authors if they are empty or None
                if not existing_paper.authors and paper_data.get('authors'):
                    existing_paper.authors = paper_data['authors']
                    session.commit()
                    print(f"Updated authors for paper: {existing_paper.title}")
                return  # Skip saving the paper as it already exists


            else:
                # Add new paper record
                paper = Papers(
                    title=paper_data['title'],
                    category=paper_data['category'],
                    pub_date=paper_data['published_date'],
                    authors=paper_data['authors'],
                    url=paper_data['url'],
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


    def process_papers(self, query: str, category: str,  batch_size: int=100, download_dir: str = './store'):
        """
        Process papers in batches by downloading, fetching their contents, and storing them in the database and MongoDB.

        Parameters:
        - query (str): The search term to query arXiv.
        - category (str): The category to use for storage and processing.
        - download_dir (str): Directory to store downloaded papers.
        - batch_size (int): Number of papers to fetch and process per batch.
        """
        offset = 0  # Start offset for pagination
        while True:
            # Clean the download directory before starting the batch
            self.clean_download_directory(download_dir)

            # Initialize the downloader with the current batch
            downloader = ArxivPaperDownloader(query=query, max_results=batch_size, download_dir=download_dir)
            downloaded_papers = downloader.download_papers()

            # Stop if no papers were downloaded (end of available results)
            if not downloaded_papers:
                print("No more papers to download. Processing completed.")
                break

            # Define required fields for completeness check.
            required_fields = ["title", "authors", "published_date", "keywords", "url", "summary", "content"]

            for paper in downloaded_papers:
                print(f"Processing paper: {paper['title']}")

                # Check if the paper already exists and is complete in MongoDB
                if self.mongo_manager.is_document_complete(
                    collection_name=category,
                    title=paper['title'],
                    required_fields=required_fields
                ):
                    print(f"Paper '{paper['title']}' already exists and is complete in MongoDB. Skipping.")
                    continue

                # Fetch paper content
                fetcher = ArxivPaperFetcher(title_query=paper['title'])
                fetcher.fetch_paper()
                content = fetcher.get_content()

                if content:
                    # Extract keywords
                    keywords = self.extract_keywords(content)

                    # Store content in MongoDB vector store
                    document = Document(
                        page_content=content,
                        metadata={
                            "title": fetcher.get_title(),
                            "authors": fetcher.get_authors(),
                            "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                            "keywords": keywords,
                            "url": fetcher.get_links(),
                            "summary": fetcher.get_summary(),
                            "content": content
                        }
                    )
                    if self.mongo_manager.document_exists(collection_name=category, title=paper['title']):
                        print(f"Paper '{paper['title']}' already exists in MongoDB. Updating metadata...")
                        self.mongo_manager.single_update_document(
                            collection_name=category, title=paper['title'], updated_metadata=document.metadata
                        )
                    else:
                        print(f"Paper '{paper['title']}' does not exist in MongoDB. Storing new document...")
                        self.mongo_manager.store_document(collection_name=category, document=document)
                        print(f"Document stored in MongoDB collection '{category}'.")

                    # Create the indexes for search and vector search
                    self.mongo_manager.create_indexes(collection_name=category)

                    # Save paper metadata to SQL database
                    paper_data = {
                        "title": fetcher.get_title(),
                        "category": category,
                        "authors": fetcher.get_authors(),
                        "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                        "url": fetcher.get_links(),
                        "keywords": keywords,
                        "collection_name": category,
                        "is_processed": True
                    }

                    with get_session_with_ctx_manager() as session:
                        self.save_paper_metadata(session, paper_data)
                else:
                    print(f"No content found for paper: {paper['title']}")

            # Increment the offset for the next batch
            offset += batch_size


# # Example Usage
# if __name__ == "__main__":
#     pipeline = PapersPipeline(mongo_uri=MONGODB_ATLAS_CLUSTER_URI, mongo_db_name=MONGO_DB_NAME)
#     pipeline.process_papers(query="physics", category="physics", download_dir='./store')


if __name__ == "__main__":
    # List of categories to process
    arxiv_categories = {
        "physics": "Physics",
        "math": "Mathematics",
        "cs": "Computer Science",
        "eess": "Electrical Engineering and Systems Science",
        "econ": "Economics",
        "q-bio": "Quantitative Biology",
        "q-fin": "Quantitative Finance",
        "stat": "Statistics"
    }


    # Create an instance of PapersPipeline
    pipeline = PapersPipeline(mongo_uri=MONGODB_ATLAS_CLUSTER_URI, mongo_db_name=MONGO_DB_NAME)

    # Process papers for each category
    for key, full_name in arxiv_categories.items():
        print(f"\nProcessing category: {full_name} ({key})")
        try:
            pipeline.process_papers(query=key, category=str(full_name.lower()), download_dir='./store')
        except Exception as e:
            print(f"Error processing category {full_name} ({key}): {e}")




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



    def clean_download_directory(self, download_dir: str):
        """
        Empties the specified directory to prepare it for the next batch of downloads.

        Parameters:
        - download_dir (str): The directory to clean.
        """
        if os.path.exists(download_dir):
            for filename in os.listdir(download_dir):
                file_path = os.path.join(download_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            os.makedirs(download_dir)


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
                

                if not existing_paper.url and paper_data.get('url'):
                    existing_paper.url = paper_data['url']
                    session.commit()
                    print(f"Updated url for paper: {existing_paper.title}")

                # Update authors if they are empty or None
                if not existing_paper.authors and paper_data.get('authors'):
                    existing_paper.authors = paper_data['authors']
                    session.commit()
                    print(f"Updated authors for paper: {existing_paper.title}")
                return  # Skip saving the paper as it already exists


            else:
                # Add new paper record
                paper = Papers(
                    title=paper_data['title'],
                    category=paper_data['category'],
                    pub_date=paper_data['published_date'],
                    authors=paper_data['authors'],
                    url=paper_data['url'],
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


    def process_papers(self, query: str, category: str, batch_size: int = 100, download_dir: str = './store', sources: Optional[List[str]] = None):
        """
        Processes papers from various sources in batches by downloading, fetching their contents, and storing them in the database and MongoDB. If sources is not specified,
        use all available sources: arxiv, elsevier, and springer.

        Parameters:
        - query (str): The search term to query arXiv.
        - category (str): The category to use for storage and processing.
        - download_dir (str): Directory to store downloaded papers.
        - batch_size (int): Number of papers to fetch and process per batch.
        - sources (List[str]): List of sources to process. Defaults to ["arxiv", "elsevier", "springer"].
        """
        if sources is None:
            sources = ["arxiv", "elsevier", "springer"]
        print(f"Processing papers for query: {query} from sources: {sources}")

        # For demonstration, we process each source sequentially.
        for source in sources:
            if source.lower() == "arxiv":
                offset = 0  # Start offset for pagination
                while True:
                    # Clean the download directory before starting the batch
                    self.clean_download_directory(download_dir)

                    # Initialize the downloader with the current batch
                    downloader = ArxivPaperDownloader(query=query, max_results=batch_size, download_dir=download_dir)
                    downloaded_papers = downloader.download_papers()

                    # Stop if no papers were downloaded (end of available results)
                    if not downloaded_papers:
                        print("No more papers to download. Processing completed.")
                        break

                    # Define required fields for completeness check.
                    required_fields = ["title", "authors", "published_date", "keywords", "url", "summary", "content"]

                    for paper in downloaded_papers:
                        print(f"Processing paper: {paper['title']}")

                        # Check if the paper already exists and is complete in MongoDB
                        if self.mongo_manager.is_document_complete(
                            collection_name=category,
                            title=paper['title'],
                            required_fields=required_fields
                        ):
                            print(f"Paper '{paper['title']}' already exists and is complete in MongoDB. Skipping.")
                            continue

                        # Fetch paper content
                        fetcher = ArxivPaperFetcher(title_query=paper['title'])
                        fetcher.fetch_paper()
                        content = fetcher.get_content()

                        if content:
                            # Extract keywords
                            keywords = self.extract_keywords(content)

                            # Store content in MongoDB vector store
                            document = Document(
                                page_content=content,
                                metadata={
                                    "title": fetcher.get_title(),
                                    "authors": fetcher.get_authors(),
                                    "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                                    "keywords": keywords,
                                    "url": fetcher.get_links(),
                                    "summary": fetcher.get_summary(),
                                    "content": content
                                }
                            )
                            if self.mongo_manager.document_exists(collection_name=category, title=paper['title']):
                                print(f"Paper '{paper['title']}' already exists in MongoDB. Updating metadata...")
                                self.mongo_manager.single_update_document(
                                    collection_name=category, title=paper['title'], updated_metadata=document.metadata
                                )
                            else:
                                print(f"Paper '{paper['title']}' does not exist in MongoDB. Storing new document...")
                                self.mongo_manager.store_document(collection_name=category, document=document)
                                print(f"Document stored in MongoDB collection '{category}'.")

                            # Create the indexes for search and vector search
                            self.mongo_manager.create_indexes(collection_name=category)

                            # Save paper metadata to SQL database
                            paper_data = {
                                "title": fetcher.get_title(),
                                "category": category,
                                "authors": fetcher.get_authors(),
                                "published_date": datetime.strptime(fetcher.get_published_date(), "%Y-%m-%d"),
                                "url": fetcher.get_links(),
                                "keywords": keywords,
                                "collection_name": category,
                                "is_processed": True
                            }

                            with get_session_with_ctx_manager() as session:
                                self.save_paper_metadata(session, paper_data)
                        else:
                            print(f"No content found for paper: {paper['title']}")

                    # Increment the offset for the next batch
                    offset += batch_size
            elif source.lower() == "elsevier":
                # Instantiate the ElsevierPaperFetcher with your query and result limit.
                elsevier_fetcher = ElsevierPaperFetcher(title_query=query, limit_results=batch_size)

                # Fetch paper metadata from Elsevier – this returns lists of DOIs, full text URLs, and a list of metadata dicts.
                doi_list, full_text_urls, metadata_list = elsevier_fetcher.fetch_paper()

                for meta in metadata_list:
                    print(f"Processing Elsevier paper: {meta['title']}")
                    
                    # If a valid URL is present, try to fetch the full document.
                    if meta['url'] and meta['url'] != "URL not available":
                        # Passing both DOI and URL to fetch_full_document so it can try with DOI first.
                        document_text = elsevier_fetcher.fetch_full_document(doi=meta.get("doi"), uri=meta.get("url"))
                        if document_text:
                            # Process the document text (e.g. extract keywords)
                            keywords = self.extract_keywords(document_text)
                            # Save the paper metadata using a database session 
                            with get_session_with_ctx_manager() as session:
                                self.save_paper_metadata(session, {
                                    "title": meta['title'],
                                    "category": category,
                                    "published_date": datetime.strptime(meta['published_date'], "%Y-%m-%d") 
                                    if meta['published_date'] != "Publication date not available" 
                                    else datetime(1900, 1, 1),
                                    "authors": meta['authors'],
                                    "url": meta['url'],
                                    "keywords": keywords,
                                    "collection_name": category,
                                    "is_processed": True
                                })
                            # Create a Document object 
                            doc = Document(page_content=document_text, metadata=meta)
                            print(f"Fetched page content for Elsevier paper '{meta['title']}': {document_text[:300]}...")
                        else:
                            print(f"No full document text retrieved for Elsevier paper '{meta['title']}'.")

                    # Check whether the document already exists in MongoDB.
                    if self.mongo_manager.document_exists(collection_name=category, title=meta['title']):
                        print(f"Elsevier paper '{meta['title']}' already exists in MongoDB. Updating metadata...")
                        self.mongo_manager.single_update_document(
                            collection_name=category, title=meta['title'], updated_metadata={"url": meta['url']}
                        )
                    else:
                        print(f"Elsevier paper '{meta['title']}' does not exist in MongoDB. Storing new document...")
                        # If we haven’t already created a Document object (because we couldn’t fetch text), we create one now.
                        if 'doc' not in locals():
                            doc = Document(page_content="", metadata=meta)
                        self.mongo_manager.store_document(collection_name=category, document=doc)
                        print(f"Document stored in MongoDB collection '{category}'.")

            elif source.lower() == "springer":
                # Instantiate the SpringerPaperFetcher with your query and (optionally) a limit
                springer_fetcher = SpringerPaperFetcher(query=query)
                articles_metadata = springer_fetcher.fetch_articles()

                for article in articles_metadata:
                    print(f"Processing Springer paper: {article['title']}")
                    
                    # Save the metadata (without the full text) into your relational or metadata store
                    with get_session_with_ctx_manager() as session:
                        self.save_paper_metadata(session, {
                            "title": article['title'],
                            "category": category,
                            # We expect the published date to be in YYYY-MM-DD format;
                            # if not available, we default to January 1, 1900.
                            "published_date": datetime.strptime(article['published_date'], "%Y-%m-%d")
                                if article['published_date'] != "Published date not found" else datetime(1900, 1, 1),
                            "authors": article['authors'],
                            "url": article['url'],
                            "keywords": [],  # (Insert keyword extraction if needed)
                            "collection_name": category,
                            "is_processed": True
                        })
                    
                    # For Springer we already parse the <body> content into the "content" key.
                    if article.get("content") and article.get("content") != "No body content found":
                        # Create a Document using the full text content and the metadata.
                        doc = Document(page_content=article["content"], metadata=article)
                        # Print a preview of the content (first 300 characters)
                        print(f"Fetched page content for Springer paper '{article['title']}': {article['content'][:300]}...")
                        
                        # Store the document into MongoDB (update if already exists)
                        if self.mongo_manager.document_exists(collection_name=category, title=article['title']):
                            print(f"Springer paper '{article['title']}' already exists in MongoDB. Updating metadata...")
                            self.mongo_manager.single_update_document(
                                collection_name=category,
                                title=article['title'],
                                updated_metadata={"url": article['url']}
                            )
                        else:
                            print(f"Springer paper '{article['title']}' does not exist in MongoDB. Storing new document...")
                            self.mongo_manager.store_document(collection_name=category, document=doc)
                            print(f"Document stored in MongoDB collection '{category}'.")
                    else:
                        print(f"No full document content available for Springer paper '{article['title']}'.")

# Example usage:
if __name__ == "__main__":
    from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
    pipeline = PapersPipeline(
        mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
        mongo_db_name=MONGO_DB_NAME,
    )
    pipeline.process_papers(query="quantum energy", category="physics", download_dir="./store", batch_size=5)