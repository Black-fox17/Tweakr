import os
import random
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from datapipeline.main import PapersPipeline
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import time

logging.basicConfig(level=logging.INFO)

class PipelineManager:
    def __init__(self):
        self.mongo_manager = MongoDBVectorStoreManager(
            connection_string=MONGODB_ATLAS_CLUSTER_URI,
            db_name=MONGO_DB_NAME
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=None,
            timeout=None,
            max_retries=2
        )
        self.pipeline = PapersPipeline(
            mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
            mongo_db_name=MONGO_DB_NAME
        )
        
        # Define categories and their associated keywords
        self.categories = {
            "machine_learning": ["deep learning", "neural networks", "reinforcement learning", "computer vision", "nlp"],
            "artificial_intelligence": ["ai", "machine intelligence", "cognitive computing", "robotics", "expert systems"],
            "data_science": ["big data", "data mining", "predictive analytics", "statistics", "data visualization"],
            "computer_science": ["algorithms", "data structures", "software engineering", "distributed systems", "cybersecurity"],
            "physics": ["quantum mechanics", "particle physics", "astrophysics", "condensed matter", "cosmology"],
            "biology": ["genetics", "molecular biology", "ecology", "evolution", "biotechnology"],
            "chemistry": ["organic chemistry", "inorganic chemistry", "physical chemistry", "analytical chemistry", "biochemistry"],
            "mathematics": ["algebra", "calculus", "statistics", "topology", "number theory"]
        }
        
        # Define sources to use
        self.sources = ["elsevier", "springer"]
        
        # Define batch sizes for each source
        self.batch_sizes = {
            "elsevier": 5,
            "springer": 5
        }

    def generate_random_query(self, category: str) -> str:
        """
        Generate a random query for a given category using Gemini.
        """
        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in academic research. Generate a specific research query for the given category."),
                ("human", "Generate a specific research query for {category} category. The query should be focused and academic.")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"category": category})
            
            if isinstance(response, dict) and "content" in response:
                return response["content"].strip()
            return str(response).strip()
        except Exception as e:
            logging.error(f"Error generating query for {category}: {e}")
            # Fallback to random keyword if Gemini fails
            return random.choice(self.categories.get(category, ["research"]))

    def get_existing_categories(self) -> List[str]:
        """
        Get list of existing categories from MongoDB.
        """
        try:
            collections = self.mongo_manager.db.list_collection_names()
            return [col for col in collections if col in self.categories]
        except Exception as e:
            logging.error(f"Error getting existing categories: {e}")
            return []

    def get_category_stats(self, category: str) -> Dict:
        """
        Get statistics for a category.
        """
        try:
            collection = self.mongo_manager.get_or_create_collection(category)
            count = collection.count_documents({})
            return {
                "category": category,
                "document_count": count,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logging.error(f"Error getting stats for category {category}: {e}")
            return {}

    def process_category(self, category: str, force_update: bool = False):
        """
        Process papers for a specific category.
        """
        try:
            # Check if category needs processing
            stats = self.get_category_stats(category)
            if not force_update and stats.get("document_count", 0) > 100:
                logging.info(f"Category {category} has sufficient documents. Skipping.")
                return

            # Generate random query
            query = self.generate_random_query(category)
            logging.info(f"Generated query for {category}: {query}")

            # Process papers for each source
            for source in self.sources:
                try:
                    self.pipeline.process_papers(
                        query=query,
                        category=category,
                        batch_size=self.batch_sizes[source],
                        sources=[source]  # Process one source at a time
                    )
                    logging.info(f"Completed processing for {category} from {source}")
                except Exception as e:
                    logging.error(f"Error processing {category} from {source}: {e}")
                    continue

            logging.info(f"Completed processing for category {category}")
        except Exception as e:
            logging.error(f"Error processing category {category}: {e}")

    def run_automated_pipeline(self, force_update: bool = False):
        """
        Run the automated pipeline for all categories.
        """
        try:
            # Get existing categories
            existing_categories = self.get_existing_categories()
            
            # Process each category
            for category in self.categories:
                try:
                    if category not in existing_categories or force_update:
                        logging.info(f"Processing category: {category}")
                        self.process_category(category, force_update)
                    else:
                        logging.info(f"Skipping category {category} - already exists")
                except Exception as e:
                    logging.error(f"Error processing category {category}: {e}")
                    continue

            logging.info("Automated pipeline completed successfully")
        except Exception as e:
            logging.error(f"Error in automated pipeline: {e}")

    def schedule_pipeline(self, interval_hours: int = 24):
        """
        Schedule the pipeline to run at regular intervals.
        """
        while True:
            try:
                self.run_automated_pipeline()
                logging.info(f"Pipeline completed. Next run in {interval_hours} hours.")
                time.sleep(interval_hours * 3600)  # Convert hours to seconds
            except Exception as e:
                logging.error(f"Error in scheduled pipeline: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

# if __name__ == "__main__":
#     manager = PipelineManager()
#     # Run once immediately
#     manager.run_automated_pipeline()
#     # Then schedule regular runs
#     manager.schedule_pipeline(interval_hours=24) 