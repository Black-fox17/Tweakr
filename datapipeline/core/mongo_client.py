import os
from pymongo import MongoClient
# from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_mongodb import MongoDBAtlasVectorSearch
# from langchain_community.embeddings import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.docstore.document import Document


from datapipeline.core.extract_contents_arxiv_paper import ArxivPaperFetcher
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME


class MongoDBVectorStoreManager:
    def __init__(self, connection_string: str = MongoDBAtlasVectorSearch, db_name: str = MONGO_DB_NAME):
        """
        Initializes the MongoDB connection.

        Parameters:
        - connection_string (str): MongoDB connection URI.
        - db_name (str): Name of the database.
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]

    def document_exists(self, collection_name: str, title: str) -> bool:
        """
        Check if a document with the given title exists in the specified MongoDB collection.
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.find_one({"metadata.title": title}) is not None

    def get_or_create_collection(self, collection_name: str):
        """
        Checks if a collection exists; if not, creates it.

        Parameters:
        - collection_name (str): Name of the collection.

        Returns:
        - Collection: The MongoDB collection object.
        """
        if collection_name not in self.db.list_collection_names():
            self.db.create_collection(collection_name)
        return self.db[collection_name]

    def store_document(self, collection_name: str, document: Document):
        """
        Stores a document in the specified collection with vector embeddings.

        Parameters:
        - collection_name (str): Name of the collection.
        - document (Document): The document to store.
        """
        collection = self.get_or_create_collection(collection_name)
        # Swapped the embedding for google's embeddings
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        # embeddings = OpenAIEmbeddings()
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name=f"{collection_name}_index"
        )
        vector_store.add_documents([document])

# Example usage:
# if __name__ == "__main__":
#     # Fetch paper content
#     paper_title = "Bit symmetry entails the symmetry of the quantum transition probability"
#     fetcher = ArxivPaperFetcher(title_query=paper_title)
#     fetcher.fetch_paper()
#     content = fetcher.get_content()

#     if content:
#         # Initialize MongoDB manager
#         mongo_uri = MONGODB_ATLAS_CLUSTER_URI
#         db_name = MONGO_DB_NAME
#         category = "quantum_physics"  # Example category; adjust as needed

#         mongo_manager = MongoDBVectorStoreManager(connection_string=mongo_uri, db_name=db_name)

#         # Create a Document object
#         document = Document(
#             page_content=content,
#             metadata={
#                 "title": fetcher.get_title(),
#                 "authors": fetcher.get_authors(),
#                 "published_date": fetcher.get_published_date(),
#                 "summary": fetcher.get_summary()
#             }
#         )

#         # Store document in the vector store
#         mongo_manager.store_document(collection_name=category, document=document)
#         print(f"Document stored in collection '{category}'.")
#     else:
#         print("No content fetched to store.")
