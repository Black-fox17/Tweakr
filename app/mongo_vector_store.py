import os
from pymongo import MongoClient, UpdateOne
from pymongo.operations import SearchIndexModel
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_mongodb.retrievers.hybrid_search import MongoDBAtlasHybridSearchRetriever
from typing import List
from langchain.docstore.document import Document

from app.core.constants import MONGO_DB_URL
from app.monitoring.services import logger
# from app.core.mongodb_client import MongoDBClient


class MongoDBVectorStoreManager:
    def __init__(
        self,
        embedding_model,
        connection_string: str = MONGO_DB_URL,
        db_name: str = "listen-ai-scripts",
        collection_name: str = "scripts",
    ):
        """
        Initializes the MongoDB connection.

        Parameters:
        - connection_string (str): MongoDB connection URI.
        - db_name (str): Name of the database.
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.embedding_model = embedding_model
        self.collection_name = collection_name

    def document_exists(self, title: str) -> bool:
        """
        Check if a document with the given title exists in the specified MongoDB collection.
        """
        collection = self.get_or_create_collection()
        return collection.find_one({"metadata.title": title}) is not None

    def get_or_create_collection(self):
        """
        Checks if a collection exists; if not, creates it.

        Parameters:
        - collection_name (str): Name of the collection.

        Returns:
        - Collection: The MongoDB collection object.
        """
        if self.collection_name not in self.db.list_collection_names():
            self.db.create_collection(self.collection_name)
        return self.db[self.collection_name]


    def initialize_vectorstore(self, documents: List[Document]) -> MongoDBAtlasVectorSearch:
        """
        Stores a document in the specified collection with vector embeddings, creating the required indexes if necessary.

        Parameters:
        - documents (List[Document]): List of documents to store.
        """
        collection = self.get_or_create_collection()

        # Store Document
        try:
            logger.info("Storing document in vector store...")
            index_name = f"{self.collection_name}_index"
            vector_store = MongoDBAtlasVectorSearch(
                collection=collection, 
                embedding=self.embedding_model,
                index_name=index_name,
                relevance_score_fn="cosine"
            )

            # Check if the index already exists
            existing_indexes = [idx["name"] for idx in collection.list_indexes()]
            logger.info(f"Existing indexes: {existing_indexes}")  # Debugging: Log existing indexes

            if index_name not in existing_indexes:
                logger.info(f"Creating vector search index: {index_name}...")
                vector_store.create_vector_search_index(dimensions=1536)
            else:
                logger.info(f"Vector search index '{index_name}' already exists. Skipping creation.")

            vector_store.add_documents(documents)
            logger.info("Documents stored successfully.")
            return vector_store  # Return the created vector store
        except Exception as e:
            logger.error(f"Error storing document in vector store: {e}")
            return None

    # def initialize_vectorstore(self, documents: List[Document]) -> MongoDBAtlasVectorSearch:
    #     """
    #     Stores a document in the specified collection with vector embeddings, creating the required indexes if necessary.

    #     Parameters:
    #     - collection_name (str): Name of the collection.
    #     - document (Document): The document to store.
    #     """
    #     collection = self.get_or_create_collection()

    #     # Store Document
    #     try:
    #         logger.info("Storing document in vector store...")
    #         index_name = f"{self.collection_name}_index"
    #         vector_store = MongoDBAtlasVectorSearch(
    #             collection=collection, 
    #             embedding=self.embedding_model,
    #             index_name = index_name,
    #             relevance_score_fn = "cosine"
    #         )
    #         # Check if the index already exists
    #         existing_indexes = [idx["name"] for idx in collection.list_indexes()]
    #         if index_name not in existing_indexes:
    #             logger.info(f"Creating vector search index: {index_name}...")
    #             vector_store.create_vector_search_index(dimensions=1536)
    #         else:
    #             logger.info(f"Vector search index '{index_name}' already exists. Skipping creation.")
    #         vector_store.add_documents(documents)
    #         logger.info(f"Document stored successfully.")
    #         return vector_store  # Return the created vector store
    #     except Exception as e:
    #         logger.error(f"Error storing document in vector store: {e}")

    def create_indexes(self):
        """
        Creates the required indexes for the MongoDB collection if they don't already exist.

        Parameters:
        - collection_name (str): Name of the collection.
        """
        collection = self.get_or_create_collection()

        # Check existing indexes
        existing_indexes = [index["name"] for index in collection.list_indexes()]

        # Create Atlas Search Index
        search_index_name = f"{self.collection_name}_search_index"
        if search_index_name not in existing_indexes:
            try:
                logger.info(f"Creating search index '{search_index_name}'...")
                search_index_model = SearchIndexModel(
                    definition={"mappings": {"dynamic": True}},
                    name=search_index_name,
                )
                collection.create_search_index(model=search_index_model)
                logger.info(f"Search index '{search_index_name}' created successfully.")
            except Exception as e:
                logger.warning(
                    f"Could not create search index '{search_index_name}': {e}"
                )
        else:
            logger.info(
                f"Search index '{search_index_name}' already exists. Skipping creation."
            )

        # Create Vector Search Index
        vector_index_name = f"{self.collection_name}_vector_index"
        if vector_index_name not in existing_indexes:
            try:
                logger.info(f"Creating vector search index '{vector_index_name}'...")
                vector_search_index_model = SearchIndexModel(
                    definition={
                        "fields": [
                            {
                                "type": "vector",
                                "numDimensions": 768,
                                "path": "text",
                                "similarity": "cosine",
                            },
                        ]
                    },
                    name=vector_index_name,
                    type="vectorSearch",
                )
                collection.create_search_index(model=vector_search_index_model)
                logger.info(
                    f"Vector search index '{vector_index_name}' created successfully."
                )
            except Exception as e:
                logger.warning(
                    f"Could not create vector search index '{vector_index_name}': {e}"
                )
        else:
            logger.info(
                f"Vector search index '{vector_index_name}' already exists. Skipping creation."
            )

    def update_documents(self, updates: list[dict]):
        """
        Updates multiple documents in a batch operation.

        Parameters:
        - collection_name (str): MongoDB collection name.
        - updates (list): A list of dictionaries with 'title' and 'updated_metadata'.
        """
        collection = self.get_or_create_collection()

        bulk_operations = [
            UpdateOne(
                {"metadata.title": update["title"]},
                {
                    "$set": {
                        f"metadata.{key}": value
                        for key, value in update["updated_metadata"].items()
                    }
                },
            )
            for update in updates
        ]

        if bulk_operations:
            result = collection.bulk_write(bulk_operations)
            print(
                f"Batch update complete. Matched: {result.matched_count}, Modified: {result.modified_count}"
            )

    def single_update_document(
        self, title: str, updated_metadata: dict
    ):
        """
        Updates a document's metadata in the MongoDB collection.

        Parameters:
        - collection_name (str): Name of the collection.
        - title (str): Title of the document to identify it.
        - updated_metadata (dict): The updated metadata to set.
        """
        collection = self.get_or_create_collection()
        query = {"metadata.title": title}  # Query by title
        update_fields = {
            "$set": {
                f"metadata.{key}": value for key, value in updated_metadata.items()
            }
        }

        # Perform the update
        result = collection.update_one(query, update_fields)

        if result.matched_count:
            print(f"Document '{title}' updated successfully.")
        else:
            print(f"Document '{title}' not found. No updates performed.")

    def get_document(self, title: str) -> dict:
        """
        Retrieves a document from the MongoDB collection by title.

        Parameters:
        - collection_name (str): Name of the collection.
        - title (str): Title of the document to fetch.

        Returns:
        - dict: The document retrieved, or None if not found.
        """
        collection = self.get_or_create_collection()
        document = collection.find_one({"metadata.title": title})
        return document

    def is_document_complete(
        self, title: str, required_fields: list
    ) -> bool:
        """
        Checks if a document has all required fields populated.

        Parameters:
        - collection_name (str): The collection to check.
        - title (str): The title of the document.
        - required_fields (list): List of required fields to verify completeness.

        Returns:
        - bool: True if the document is complete, False otherwise.
        """
        collection = self.get_or_create_collection()
        document = collection.find_one({"metadata.title": title})

        if not document:
            return False  # Document does not exist

        # Check if all required fields are present and not empty
        metadata = document.get("metadata", {})
        return not any(
            field not in metadata or not metadata[field] for field in required_fields
        )

    def generate_query_embedding(self, query: str) -> list:
        return embeddings(query)

    def semantic_search(
        self,
        collection_name: str,
        query_text: str,
        top_k: int = 1,
        fulltext_penalty: float = 60.0,
        vector_penalty: float = 60.0,
    ):
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
            collection = self.get_or_create_collection()
            vector_store = MongoDBAtlasVectorSearch(
                collection=collection,
                embedding=self.embeddings_model,
                relevance_score_fn="cosine",
            )

            
            search_index_name = f"{self.collection_name}_search_index"
            retriever = MongoDBAtlasHybridSearchRetriever(
                vectorstore=vector_store,
                search_index_name=search_index_name,
                top_k=top_k,
                fulltext_penalty=fulltext_penalty,
                vector_penalty=vector_penalty,
            )

            
            documents = retriever.invoke(query_text)
            logger.info(f"Retrieved {len(documents)} documents.")

            for doc in documents:
                logger.info(f"Document: {doc}")

            return documents

        except Exception as e:
            logger.error(f"Error during semantic search: {e}")
            return []

    def retrieve_results(
        self,

    ):
        pass


# if __name__ == "__main__":
#     mongo = MongoDBVectorStoreManager()
#     try:
#         results = mongo.semantic_search(
#             "quantum_physics",
#             query_text="Advances in modern physics and technology have spurred great interest in the study of symmetry and topology in condensed matter physics",
#             top_k=3,
#         )
#         for r in results:
#             print("Title:", r.metadata["title"], "Score:", r.metadata["score"])
#     except Exception as e:
#         print(f"Error during semantic search: {e}")
