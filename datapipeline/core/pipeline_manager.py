import os
import random
import logging
from typing import List, Dict, Optional, Union, Set
from datetime import datetime, timedelta
from datapipeline.main import PapersPipeline
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class PipelineManager:
    def __init__(self, random_category_count: int = 3):
        """
        Initialize the PipelineManager.
        
        Parameters:
        - random_category_count: Number of random categories to generate when requested
        """
        # Initialize MongoDB connection
        self.mongo_manager = MongoDBVectorStoreManager(
            connection_string=MONGODB_ATLAS_CLUSTER_URI,
            db_name=MONGO_DB_NAME
        )
        
        # Initialize LLM for generating queries and categories
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.7,
            max_tokens=None,
            timeout=None,
            max_retries=3
        )
        
        # Initialize the papers pipeline
        self.pipeline = PapersPipeline(
            mongo_uri=MONGODB_ATLAS_CLUSTER_URI,
            mongo_db_name=MONGO_DB_NAME
        )
        
        # Number of random categories to generate
        self.random_category_count = random_category_count
        
        # Define predefined categories and their associated keywords
        self.predefined_categories = {
            "machine_learning": ["deep learning", "neural networks", "reinforcement learning", "computer vision", "nlp"],
            "artificial_intelligence": ["ai", "machine intelligence", "cognitive computing", "robotics", "expert systems"],
            "data_science": ["big data", "data mining", "predictive analytics", "statistics", "data visualization"],
            "computer_science": ["algorithms", "data structures", "software engineering", "distributed systems", "cybersecurity"],
            "physics": ["quantum mechanics", "particle physics", "astrophysics", "condensed matter", "cosmology"],
            "biology": ["genetics", "molecular biology", "ecology", "evolution", "biotechnology"],
            "chemistry": ["organic chemistry", "inorganic chemistry", "physical chemistry", "analytical chemistry", "biochemistry"],
            "mathematics": ["algebra", "calculus", "statistics", "topology", "number theory"],
            "medicine": ["clinical trials", "public health", "oncology", "immunology", "neurology"],
            "environmental_science": ["climate change", "sustainability", "ecology", "pollution", "conservation"]
        }
        
        # Store dynamically generated categories
        self.dynamic_categories = {}
        
        # All active categories (predefined + dynamic)
        self.active_categories = self.predefined_categories.copy()
        
        # Define sources to use
        self.sources = ["elsevier", "springer", "arxiv", "pubmed"]
        
        # Define batch sizes for each source
        self.batch_sizes = {
            "elsevier": 5,
            "springer": 5,
            "arxiv": 8,
            "pubmed": 6
        }
        
        # Track processing metrics
        self.metrics = {
            "categories_processed": 0,
            "papers_added": 0,
            "failed_categories": [],
            "last_run": None
        }

    def generate_random_query(self, category: str) -> str:
        """
        Generate a random query for a given category using LLM.
        
        Parameters:
        - category: The category to generate a query for
        
        Returns:
        - A specific research query string for the category
        """
        try:
            logging.info(f"Generating random query for category: {category}")
            
            # Use keywords from category if available
            keywords = ""
            if category in self.active_categories and self.active_categories[category]:
                keywords = ", ".join(self.active_categories[category])
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in academic research specializing in generating targeted search queries."),
                ("human", f"""Generate a specific academic research query for the '{category}' category. 
                The query should be focused, precise, and suitable for retrieving relevant academic papers.
                Related keywords: {keywords}
                
                Respond with ONLY the query, no explanations or other text.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({"category": category})
            
            # Extract query from response
            if isinstance(response, dict) and "content" in response:
                query = response["content"].strip()
            else:
                query = str(response).strip()
            
            # Clean up any quotation marks or formatting
            query = query.strip('"\'').strip()
            
            logging.info(f"Generated query for {category}: {query}")
            return query
            
        except Exception as e:
            logging.error(f"Error generating query for {category}: {e}")
            # Fallback to random keyword if LLM fails
            if category in self.active_categories and self.active_categories[category]:
                fallback_query = f"{category} {random.choice(self.active_categories[category])}"
            else:
                fallback_query = f"{category} research recent developments"
                
            logging.info(f"Using fallback query for {category}: {fallback_query}")
            return fallback_query

    def generate_random_categories(self, count: int = None) -> Dict[str, List[str]]:
        """
        Generate random academic categories using LLM.
        
        Parameters:
        - count: Number of categories to generate (defaults to self.random_category_count)
        
        Returns:
        - Dictionary of category names and associated keywords
        """
        if count is None:
            count = self.random_category_count
            
        try:
            logging.info(f"Generating {count} random academic categories")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert in academic categorization and research domains."),
                ("human", f"""Generate {count} random but realistic academic research categories.
                For each category:
                1. Create a descriptive name (use snake_case for the category name)
                2. Provide 5 relevant keywords for each category
                
                Format your response as a valid Python dictionary where:
                - Keys are category names in snake_case
                - Values are lists of 5 keywords
                
                Example format:
                {{
                  "quantum_computing": ["qubits", "quantum entanglement", "quantum algorithms", "quantum gates", "superposition"],
                  "sustainable_development": ["renewable energy", "circular economy", "climate adaptation", "green infrastructure", "social equity"]
                }}
                
                Only return the Python dictionary, no other text.""")
            ])
            
            chain = prompt | self.llm
            response = chain.invoke({})
            
            # Extract dictionary from response
            if isinstance(response, dict) and "content" in response:
                content = response["content"].strip()
            else:
                content = str(response).strip()
                
            # Extract dictionary portion
            import re
            dict_match = re.search(r'\{.*\}', content, re.DOTALL)
            if dict_match:
                dict_str = dict_match.group(0)
                
                # Safely evaluate the dictionary string
                import ast
                new_categories = ast.literal_eval(dict_str)
                
                logging.info(f"Generated {len(new_categories)} random categories: {list(new_categories.keys())}")
                return new_categories
            else:
                logging.error("Failed to extract dictionary from LLM response")
                return {}
                
        except Exception as e:
            logging.error(f"Error generating random categories: {e}")
            # Fallback to simple random categories
            fallback_categories = {}
            for i in range(count):
                name = f"research_topic_{i+1}"
                fallback_categories[name] = ["research", "academic", "papers", "studies", "analysis"]
            return fallback_categories

    def add_dynamic_categories(self, count: int = None) -> List[str]:
        """
        Generate and add new dynamic categories.
        
        Parameters:
        - count: Number of categories to generate
        
        Returns:
        - List of newly added category names
        """
        new_categories = self.generate_random_categories(count)
        
        # Add to dynamic and active categories
        self.dynamic_categories.update(new_categories)
        self.active_categories.update(new_categories)
        
        return list(new_categories.keys())

    def get_existing_categories(self) -> Set[str]:
        """
        Get list of existing categories from MongoDB.
        
        Returns:
        - Set of category names that exist in the database
        """
        try:
            collections = self.mongo_manager.db.list_collection_names()
            # Filter out non-category collections
            system_collections = ["system.views", "admin", "local", "config"]
            categories = {col for col in collections if col not in system_collections}
            logging.info(f"Found {len(categories)} existing categories in database")
            return categories
        except Exception as e:
            logging.error(f"Error getting existing categories: {e}")
            return set()

    def get_category_stats(self, category: str) -> Dict:
        """
        Get statistics for a category.
        
        Parameters:
        - category: Name of the category
        
        Returns:
        - Dictionary with category statistics
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
            return {"category": category, "document_count": 0, "error": str(e)}

    def process_category(self, category: str, min_papers: int = 50, max_papers: int = 200,
                         force_update: bool = False, retry_count: int = 2) -> Dict:
        """
        Process papers for a specific category.
        
        Parameters:
        - category: Name of the category to process
        - min_papers: Minimum number of papers to maintain per category
        - max_papers: Maximum number of papers before considering category complete
        - force_update: Whether to force processing regardless of paper count
        - retry_count: Number of times to retry with different queries if needed
        
        Returns:
        - Dictionary with processing results
        """
        results = {
            "category": category,
            "papers_added": 0,
            "queries_used": [],
            "sources_processed": [],
            "status": "success"
        }
        
        try:
            # Check if category needs processing
            stats = self.get_category_stats(category)
            current_papers = stats.get("document_count", 0)
            
            if not force_update and current_papers >= max_papers:
                logging.info(f"Category {category} has sufficient documents ({current_papers}). Skipping.")
                results["status"] = "skipped"
                results["reason"] = f"Has {current_papers} papers (above maximum {max_papers})"
                return results
                
            # Determine how many papers to add
            target_papers = max(min_papers - current_papers, 10)  # Add at least 10 papers
            if target_papers <= 0 and not force_update:
                logging.info(f"Category {category} already has sufficient papers ({current_papers}). Skipping.")
                results["status"] = "skipped"
                results["reason"] = f"Has {current_papers} papers (above minimum {min_papers})"
                return results
                
            # Use multiple queries if needed
            for attempt in range(retry_count):
                # Generate random query
                query = self.generate_random_query(category)
                results["queries_used"].append(query)
                
                papers_before = self.get_category_stats(category).get("document_count", 0)
                
                # Process papers for each source
                for source in self.sources:
                    try:
                        batch_size = self.batch_sizes.get(source, 5)
                        logging.info(f"Processing {category} from {source} with query: '{query}' (batch size: {batch_size})")
                        
                        # Process papers using the pipeline
                        processed = self.pipeline.process_papers(
                            query=query,
                            category=category,
                            batch_size=batch_size,
                            sources=[source]  # Process one source at a time
                        )
                        
                        if source not in results["sources_processed"]:
                            results["sources_processed"].append(source)
                            
                        logging.info(f"Completed processing for {category} from {source}")
                        
                    except Exception as e:
                        logging.error(f"Error processing {category} from {source}: {e}")
                        continue
                
                # Check how many papers were added
                papers_after = self.get_category_stats(category).get("document_count", 0)
                papers_added = papers_after - papers_before
                results["papers_added"] += papers_added
                
                logging.info(f"Added {papers_added} papers to {category} (total: {papers_after})")
                
                # If we've added enough papers or reached the maximum, stop
                if papers_after >= min_papers or papers_after >= max_papers:
                    break
                    
                # If we didn't add many papers, try again with a different query
                if papers_added < 5 and attempt < retry_count - 1:
                    logging.info(f"Not enough papers added with query '{query}'. Trying a different query.")
                else:
                    break

            logging.info(f"Completed processing for category {category}. Added {results['papers_added']} papers.")
            return results
            
        except Exception as e:
            logging.error(f"Error processing category {category}: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
            return results

    def run_automated_pipeline(self, 
                               categories: List[str] = None,
                               include_random: bool = True, 
                               random_category_count: int = None,
                               force_update: bool = False,
                               min_papers: int = 50,
                               max_papers: int = 200) -> Dict:
        """
        Run the automated pipeline for selected categories.
        
        Parameters:
        - categories: List of specific categories to process (if None, use all active categories)
        - include_random: Whether to include randomly generated categories
        - random_category_count: Number of random categories to generate
        - force_update: Whether to force processing regardless of paper count
        - min_papers: Minimum number of papers to maintain per category
        - max_papers: Maximum number of papers before considering category complete
        
        Returns:
        - Dictionary with pipeline execution results
        """
        start_time = datetime.now()
        
        # Reset metrics for this run
        self.metrics = {
            "categories_processed": 0,
            "papers_added": 0,
            "failed_categories": [],
            "successful_categories": [],
            "start_time": start_time.isoformat(),
            "end_time": None,
            "duration_seconds": 0
        }
        
        try:
            # Get existing categories from database
            existing_categories = self.get_existing_categories()
            logging.info(f"Found {len(existing_categories)} existing categories in database")
            
            # Generate random categories if requested
            if include_random:
                count = random_category_count or self.random_category_count
                new_categories = self.add_dynamic_categories(count)
                logging.info(f"Added {len(new_categories)} new random categories: {new_categories}")
                
                # If no specific categories provided, include the new ones
                if categories is None:
                    if not categories:
                        categories = []
                    categories.extend(new_categories)
            
            # Use all active categories if none specified
            if categories is None:
                categories = list(self.active_categories.keys())
                
            logging.info(f"Starting pipeline for {len(categories)} categories")
            
            # Process each category
            results = {}
            for category in categories:
                try:
                    logging.info(f"Processing category: {category}")
                    category_results = self.process_category(
                        category, 
                        min_papers=min_papers,
                        max_papers=max_papers,
                        force_update=force_update
                    )
                    
                    results[category] = category_results
                    
                    # Update metrics
                    self.metrics["categories_processed"] += 1
                    self.metrics["papers_added"] += category_results.get("papers_added", 0)
                    
                    if category_results.get("status") == "failed":
                        self.metrics["failed_categories"].append(category)
                    else:
                        self.metrics["successful_categories"].append(category)
                        
                except Exception as e:
                    logging.error(f"Error processing category {category}: {e}")
                    results[category] = {
                        "status": "failed",
                        "error": str(e)
                    }
                    self.metrics["failed_categories"].append(category)
            
            # Update final metrics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.metrics["end_time"] = end_time.isoformat()
            self.metrics["duration_seconds"] = duration
            
            logging.info(f"Automated pipeline completed in {duration:.2f} seconds")
            logging.info(f"Processed {self.metrics['categories_processed']} categories, added {self.metrics['papers_added']} papers")
            
            if self.metrics["failed_categories"]:
                logging.warning(f"Failed categories: {self.metrics['failed_categories']}")
            
            return {
                "metrics": self.metrics,
                "results": results
            }
            
        except Exception as e:
            logging.error(f"Error in automated pipeline: {e}")
            self.metrics["end_time"] = datetime.now().isoformat()
            self.metrics["error"] = str(e)
            return {"metrics": self.metrics, "error": str(e)}

    def schedule_pipeline(self, 
                          interval_hours: int = 24,
                          include_random: bool = True,
                          random_category_count: int = 3,
                          categories_per_run: int = 5,
                          min_papers: int = 50,
                          max_papers: int = 200):
        """
        Schedule the pipeline to run at regular intervals.
        
        Parameters:
        - interval_hours: Hours between runs
        - include_random: Whether to include random categories
        - random_category_count: Number of random categories per run
        - categories_per_run: Number of categories to process each run
        - min_papers: Minimum papers per category
        - max_papers: Maximum papers per category
        """
        logging.info(f"Starting scheduled pipeline. Will run every {interval_hours} hours.")
        
        while True:
            try:
                # Select random subset of categories for this run
                all_categories = list(self.active_categories.keys())
                if len(all_categories) > categories_per_run:
                    selected_categories = random.sample(all_categories, categories_per_run)
                else:
                    selected_categories = all_categories
                
                logging.info(f"Running scheduled pipeline with {len(selected_categories)} categories")
                
                # Run the pipeline with selected categories
                results = self.run_automated_pipeline(
                    categories=selected_categories,
                    include_random=include_random,
                    random_category_count=random_category_count,
                    min_papers=min_papers,
                    max_papers=max_papers
                )
                
                logging.info(f"Pipeline run completed. Processed {results['metrics']['categories_processed']} categories.")
                logging.info(f"Next run in {interval_hours} hours.")
                
                # Sleep until next run
                time.sleep(interval_hours * 3600)  # Convert hours to seconds
                
            except Exception as e:
                logging.error(f"Error in scheduled pipeline: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying


if __name__ == "__main__":
    # Example usage
    manager = PipelineManager(random_category_count=3)
    
    # For a one-time immediate run:
    # Include both predefined and 3 random categories
    manager.run_automated_pipeline(include_random=True)
    
    # For scheduled operation:
    # Process 5 random categories from the pool, generate 2 new random categories each run
    # manager.schedule_pipeline(
    #     interval_hours=12,
    #     include_random=True,
    #     random_category_count=2,
    #     categories_per_run=5
    # )