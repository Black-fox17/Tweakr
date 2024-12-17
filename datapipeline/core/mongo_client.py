import os
from pymongo import MongoClient, UpdateOne
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

        print(f"Document '{document.metadata['title']}' stored successfully.")


    def update_document(self, collection_name: str, title: str, updated_metadata: dict):
        """
        Updates a document's metadata in the MongoDB collection.

        Parameters:
        - collection_name (str): Name of the collection.
        - title (str): Title of the document to identify it.
        - updated_metadata (dict): The updated metadata to set.
        """
        collection = self.get_or_create_collection(collection_name)
        query = {"metadata.title": title}  # Query by title
        update_fields = {"$set": {f"metadata.{key}": value for key, value in updated_metadata.items()}}

        # Perform the update
        result = collection.update_one(query, update_fields)

        if result.matched_count:
            print(f"Document '{title}' updated successfully.")
        else:
            print(f"Document '{title}' not found. No updates performed.")


    def get_document(self, collection_name: str, title: str) -> dict:
        """
        Retrieves a document from the MongoDB collection by title.

        Parameters:
        - collection_name (str): Name of the collection.
        - title (str): Title of the document to fetch.

        Returns:
        - dict: The document retrieved, or None if not found.
        """
        collection = self.get_or_create_collection(collection_name)
        document = collection.find_one({"metadata.title": title})
        return document

    def is_document_complete(self, collection_name: str, title: str, required_fields: list) -> bool:
        """
        Checks if a document has all required fields populated.

        Parameters:
        - collection_name (str): The collection to check.
        - title (str): The title of the document.
        - required_fields (list): List of required fields to verify completeness.

        Returns:
        - bool: True if the document is complete, False otherwise.
        """
        collection = self.get_or_create_collection(collection_name)
        document = collection.find_one({"metadata.title": title})

        if not document:
            return False  # Document does not exist

        # Check if all required fields are present and not empty
        metadata = document.get("metadata", {})
        for field in required_fields:
            if not metadata.get(field):  # Empty or missing field
                return False
        return True