import os
from pymongo import MongoClient, UpdateOne
from langchain_mongodb import MongoDBAtlasVectorSearch
# from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from typing import List
from langchain.docstore.document import Document


from datapipeline.core.extract_contents_arxiv_paper import ArxivPaperFetcher
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from datapipeline.core.utils import embeddings

class MongoDBVectorStoreManager:
    def __init__(self, connection_string: str = MONGODB_ATLAS_CLUSTER_URI, db_name: str = MONGO_DB_NAME):
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
        
        try:
            print("Storing document in vector store...")
            vector_store = MongoDBAtlasVectorSearch(
                collection=collection,
                embedding=embeddings,
                index_name=f"{collection_name}_index",
                relevance_score_fn = "cosine" 
            )
            vector_store.add_documents([document])
        except Exception as e:
            print(f"Error storing document in vector store: {e}")
            return
        print(f"Document '{document.metadata['title']}' stored successfully.")

    def update_documents(self, collection_name: str, updates: list[dict]):
        """
        Updates multiple documents in a batch operation.

        Parameters:
        - collection_name (str): MongoDB collection name.
        - updates (list): A list of dictionaries with 'title' and 'updated_metadata'.
        """
        collection = self.get_or_create_collection(collection_name)

        bulk_operations = [
            UpdateOne(
                {"metadata.title": update["title"]},
                {"$set": {f"metadata.{key}": value for key, value in update["updated_metadata"].items()}}
            )
            for update in updates
        ]

        if bulk_operations:
            result = collection.bulk_write(bulk_operations)
            print(f"Batch update complete. Matched: {result.matched_count}, Modified: {result.modified_count}")


    def single_update_document(self, collection_name: str, title: str, updated_metadata: dict):
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
        return not any(field not in metadata or not metadata[field] for field in required_fields)

    def similarity_search_by_vector(self, collection_name: str, query_embedding: List[float], k: int = 3):
        collection = self.get_or_create_collection(collection_name)
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,  # from your utils
            index_name=f"{collection_name}_index"
        )
        return vector_store.similarity_search(query_embedding, k=k)
        # return vector_store.as_retriever()

    def get_retriever(self, collection_name: str, search_type: str = "similarity", k: int = 1):
        """
        Retrieve a retriever for the collection with specified search parameters.

        Parameters:
        - collection_name (str): Name of the collection.
        - search_type (str): Type of search ("similarity", "mmr", "similarity_score_threshold").
        - k (int): Number of documents to retrieve.

        Returns:
        - VectorStoreRetriever: The retriever object.
        """
        collection = self.get_or_create_collection(collection_name)
        vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=embeddings,
            index_name=f"{collection_name}_index",
            relevance_score_fn="cosine",  # or use the appropriate function
        )
        retriever = vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k}
        )
        return retriever