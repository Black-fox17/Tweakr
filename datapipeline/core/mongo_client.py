import os
import logging
from pymongo import MongoClient, UpdateOne
from pymongo.operations import SearchIndexModel
from langchain_mongodb import MongoDBAtlasVectorSearch
# from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers.hybrid_search import MongoDBAtlasHybridSearchRetriever
from typing import List
from langchain.docstore.document import Document


from datapipeline.core.extract_contents_arxiv_paper import ArxivPaperFetcher
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from datapipeline.core.utils import embeddings, embeddings_model

logging.basicConfig(level=logging.INFO)

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
        Stores a document in the specified collection with vector embeddings, creating the required indexes if necessary.

        Parameters:
        - collection_name (str): Name of the collection.
        - document (Document): The document to store.
        """
        collection = self.get_or_create_collection(collection_name)

        # Store Document
        try:
            logging.info("Storing document in vector store...")
            vector_store = MongoDBAtlasVectorSearch(
                collection=collection,
                embedding=embeddings_model,
                relevance_score_fn="cosine"
            )
            vector_store.add_documents([document])
            logging.info(f"Document '{document.metadata['title']}' stored successfully.")
        except Exception as e:
            logging.error(f"Error storing document in vector store: {e}")

    
    def create_indexes(self, collection_name: str):
        """
        Creates the required indexes for the MongoDB collection.

        Parameters:
        - collection_name (str): Name of the collection.
        """
        collection = self.get_or_create_collection(collection_name)
        # Create Atlas Search Index
        search_index_name = f"{collection_name}_search_index"
        try:
            logging.info(f"Creating search index '{search_index_name}'...")
            search_index_model = SearchIndexModel(
                definition ={
                    "mappings": {
                        "dynamic": True
                    }
                },
                name=search_index_name,
            )
            collection.create_search_index(model=search_index_model)
            logging.info(f"Search index '{search_index_name}' created successfully.")
        except Exception as e:
            logging.warning(f"Search index '{search_index_name}' already exists or could not be created: {e}")

        # Create Vector Search Index
        vector_index_name = f"{collection_name}_vector_index"
        try:
            logging.info(f"Creating vector search index '{vector_index_name}'...")
            
            vector_search_index_model = SearchIndexModel(
                definition = {
                    "fields": [
                        {
                            "type": "vector",
                            "numDimensions": 768,
                            "path": "text",
                            "similarity":  "cosine"
                        },
                    ]
                },
                name=vector_index_name,
                type="vectorSearch",
            )
            collection.create_search_index(model=vector_search_index_model)
            logging.info(f"Vector search index '{vector_index_name}' created successfully.")
        except Exception as e:
            logging.warning(f"Vector search index '{vector_index_name}' already exists or could not be created: {e}")


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


    def generate_query_embedding(self, query: str) -> list:
        return embeddings(query)

    

    def semantic_search(self, collection_name: str, query_text: str, top_k: int = 1, fulltext_penalty: float = 60.0, vector_penalty: float = 60.0):
        """
        Performs a semantic search using MongoDB Atlas Hybrid Search Retriever.

        Parameters:
        - collection_name: The collection name.
        - search_index_name (str): Name of the Atlas Search index.
        - query_text (str): The search query_text.
        - top_k (int): Number of top documents to return. Default is 5.
        - fulltext_penalty (float): Penalty for full-text search. Default is 60.0.
        - vector_penalty (float): Penalty for vector search. Default is 60.0.

        Returns:
        - List[dict]: A list of retrieved documents.
        """
        try:
            collection = self.get_or_create_collection(collection_name)
            vector_store = MongoDBAtlasVectorSearch(
                collection=collection,
                embedding=embeddings_model,
                relevance_score_fn="cosine"
            )

            logging.info("Initializing MongoDB Atlas Hybrid Search Retriever...")
            search_index_name = f"{collection_name}_search_index"
            retriever = MongoDBAtlasHybridSearchRetriever(
                vectorstore=vector_store,
                search_index_name=search_index_name,
                top_k=top_k,
                fulltext_penalty=fulltext_penalty,
                vector_penalty=vector_penalty
            )

            logging.info(f"Performing hybrid search with query_text: {query_text}")
            documents = retriever.invoke(query_text)
            logging.info(f"Retrieved {len(documents)} documents.")

            for doc in documents:
                logging.info(f"Document: {doc}")

            return documents

        except Exception as e:
            logging.error(f"Error during semantic search: {e}")
            return []



            
if __name__ == "__main__":
    mongo = MongoDBVectorStoreManager()
    try:
        results = mongo.semantic_search(
            "quantum_physics",
            query_text="Advances in modern physics and technology have spurred great interest in the study of symmetry and topology in condensed matter physics", 
            top_k=3
        )
        for r in results:
            print("Title:", r.metadata["title"], "Score:", r.metadata["score"])
    except Exception as e:
        print(f"Error during semantic search: {e}")