import json
import logging
from typing import Optional, Dict, Any
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsdoc import FullDoc

from datapipeline.core.constants import ELSEVIER_API_KEY

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class ElsevierPaperFetcher:
    def __init__(self, title_query: str, config: Dict[str, str], use_scopus: bool = True, limit_results: Optional[int] = None):
        """
        Initializes the fetcher with a title query and optional result limit.
        
        Parameters:
        - title_query (str): The title or part of the title of the paper.
        - config (dict): A dictionary with keys 'apikey' and 'insttoken'.
        - use_scopus (bool): Whether to use Scopus (True) or ScienceDirect (False) for the search.
        - limit_results (int): Optional limit on the number of results to fetch. If None, fetch all.
        """
        logging.debug("Initializing ElsevierPaperFetcher")
        self.title_query = title_query
        self.document: Optional[Dict[str, Any]] = None
        self.limit_results = limit_results  # Set the limit on number of results

        # Initialize the Elsevier client using the provided configuration dictionary.
        logging.debug("Initializing ElsClient with provided API key and insttoken")
        self.client = ElsClient(config['apikey'])
        if not config['insttoken']:
            self.client.inst_token = None
            logging.warning("No insttoken provided, proceeding without it.")
        else:
            self.client.inst_token = config['insttoken']
        
        # Set search type.
        self.search_type = 'scopus' if use_scopus else 'sciencedirect'
        self.top_k = 25  # Set the number of results per page

    def fetch_paper(self):
        """
        Searches for the paper matching the title query and loads its metadata.
        """
        logging.debug(f"Fetching paper with title query: {self.title_query}")
        
        # Construct a query using the title.
        query = f"TITLE({self.title_query})"
        search = ElsSearch(query, self.search_type)

        all_results = []  # Store all results
        start = 0  # Initial offset
        total_results = None  # Keep track of total results for stopping pagination
        
        while True:
            logging.debug(f"Sending GET request to fetch papers starting at index {start}")
            search.execute(self.client, count=self.top_k)  # No `start`, rely on offset
            
            if search.results and len(search.results) > 0:
                # Append results from the current page to all_results
                all_results.extend(search.results)
                logging.debug(f"Fetched {len(search.results)} results (Total fetched: {len(all_results)})")
            else:
                logging.warning(f"No more results found starting at index {start}")
                break  # Exit the loop if no more results

            # If the result limit is set and we've fetched that many, stop
            if self.limit_results and len(all_results) >= self.limit_results:
                logging.debug(f"Fetched the limited {self.limit_results} results.")
                break

            # If we have fetched all results, stop the loop
            if total_results is None:
                total_results = search.tot_num_res
            if len(all_results) >= total_results:
                logging.debug(f"Fetched all {total_results} results.")
                break

            # Move to the next set of results (pagination)
            start += self.top_k  # Increment the offset for the next page
        
        if all_results:
            # Print the entire response
            logging.info("Full response fetched:")
            print(json.dumps(all_results, indent=2))  # Print the entire response (formatted)
            
            # Extract the DOIs and full-text URLs
            doi_list = [entry.get("prism:doi") for entry in all_results if "prism:doi" in entry]
            full_text_urls = self.extract_full_text_urls(all_results)
            logging.info(f"Extracted DOIs: {doi_list}")
            logging.info(f"Extracted Full Text URLs: {full_text_urls}")

            # Extract metadata for each result
            for result in all_results:
                title = self.extract_title(result)
                authors = self.extract_authors(result)
                pub_date = self.extract_pub_date(result)
                url = self.extract_url(result)
                logging.info(f"Title: {title}")
                logging.info(f"Authors: {authors}")
                logging.info(f"Publication Date: {pub_date}")
                logging.info(f"URL: {url}")

        else:
            logging.warning("No document found matching the title query.")

        return doi_list, full_text_urls

    def extract_full_text_urls(self, results: list) -> list:
        """
        Extracts the full-text URLs from the 'link' field where @ref='full-text'.
        """
        full_text_urls = []
        for entry in results:
            # Look for the 'link' field and extract the full-text URL if @ref='full-text'
            for link in entry.get("link", []):
                if link.get("@ref") == "full-text":
                    full_text_urls.append(link.get("@href"))
        return full_text_urls

    def extract_title(self, result: dict) -> Optional[str]:
        """
        Extracts the title of the paper.
        """
        title = result.get("dc:title")
        if title:
            return title
        return "Title not available"

    def extract_authors(self, result: dict) -> Optional[str]:
        """
        Extracts the authors of the paper.
        """
        authors = result.get("dc:creator")
        if authors:
            return authors
        return "Authors not available"

    def extract_pub_date(self, result: dict) -> Optional[str]:
        """
        Extracts the publication date of the paper.
        """
        pub_date = result.get("prism:coverDate")
        if pub_date:
            return pub_date
        return "Publication date not available"

    def extract_url(self, result: dict) -> Optional[str]:
        """
        Extracts the URL of the paper.
        """
        url = result.get("prism:url")
        if url:
            return url
        return "URL not available"


    def fetch_full_document(self, doi: str = None, uri: str = None):
        """
        Given a DOI or URI, fetch the full document using the FullDoc class.
        """
        if doi:
            logging.debug(f"Fetching full document for DOI: {doi}")
            try:
                full_doc = FullDoc(doi=doi)
                if full_doc.read(self.client):  # Fetch full document data from Elsevier
                    logging.info(f"Successfully fetched full document for DOI: {doi}")
                    print(f"Full content for DOI {doi}:")
                    print(json.dumps(full_doc.data, indent=2))  # Printing the full content
                else:
                    logging.warning(f"Failed to fetch full document for DOI: {doi}")
            except Exception as e:
                logging.error(f"Error fetching full document for DOI {doi}: {e}")

        elif uri:
            logging.debug(f"Fetching full document for URI: {uri}")
            try:
                full_doc = FullDoc(uri=uri)
                if full_doc.read(self.client):  # Fetch full document data from Elsevier
                    logging.info(f"Successfully fetched full document for URI: {uri}")
                    print(f"Full content for URI {uri}:")
                    print(json.dumps(full_doc.data, indent=2))  # Printing the full content
                else:
                    logging.warning(f"Failed to fetch full document for URI: {uri}")
            except Exception as e:
                logging.error(f"Error fetching full document for URI {uri}: {e}")

# Example usage:
if __name__ == "__main__":
    logging.debug("Starting ElsevierPaperFetcher example.")
    
    # Define configuration as a dictionary.
    config_dict = {
        "apikey": ELSEVIER_API_KEY,
        "insttoken": None  # Example: you can add your institution token if available
    }
    
    # Initialize the fetcher with a title query and the config dictionary.
    fetcher = ElsevierPaperFetcher("Quantum algorithms", config=config_dict, limit_results=5)  # Set a small limit
    doi_list, full_text_urls = fetcher.fetch_paper()

    logging.info(f"DOIs Extracted: {doi_list}")
    logging.info(f"Full Text URLs Extracted: {full_text_urls}")

    for uri in full_text_urls:
        fetcher.fetch_full_document(uri=uri)