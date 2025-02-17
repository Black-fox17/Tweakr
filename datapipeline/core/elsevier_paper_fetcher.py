import os
import re
import json
import logging
from typing import Optional, Dict, Any
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch
from elsapy.elsdoc import FullDoc

from datapipeline.core.constants import ELSEVIER_API_KEY

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a string to be used as a safe filename.
    Removes characters that are not alphanumeric, dash, underscore, or space.
    Spaces are replaced with underscores.
    """
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    sanitized = sanitized.strip().replace(" ", "_")
    return sanitized


def write_document_to_file(title: str, document_data: Any, directory: str = "temp"):
    """
    Writes the document data to a text file named after the sanitized title.
    The file is saved in the specified directory.
    """
    os.makedirs(directory, exist_ok=True)
    sanitized_title = sanitize_filename(title)
    file_path = os.path.join(directory, f"{sanitized_title}.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            if isinstance(document_data, dict):
                f.write(json.dumps(document_data, indent=2))
            else:
                f.write(str(document_data))
        logging.info(f"Document saved to: {file_path}")
    except Exception as e:
        logging.error(f"Error writing document to file {file_path}: {e}")


def filter_unwanted(original_text: str) -> str:
    """
    Filters out unwanted tokens from the original text.
    Removes tokens that start with "http" or contain "amazonaws" or "s3-",
    as well as tokens that look like filenames (e.g., ending in .pdf, .png, .jpg, .jpeg, .svg).
    """
    tokens = original_text.split()
    filtered_tokens = []
    # Pattern to detect tokens that look like filenames.
    file_pattern = re.compile(r'.*\.(pdf|png|jpg|jpeg|svg)$', re.IGNORECASE)
    for token in tokens:
        token_lower = token.lower()
        if token_lower.startswith("http"):
            continue
        if "amazonaws" in token_lower or "s3-" in token_lower:
            continue
        if file_pattern.match(token):
            continue
        filtered_tokens.append(token)
    return " ".join(filtered_tokens)


class ElsevierPaperFetcher:
    def __init__(self, title_query: str, use_scopus: bool = True, limit_results: Optional[int] = None, api_key = ELSEVIER_API_KEY):
        """
        Initializes the fetcher with a title query and optional result limit.
        
        Parameters:
        - title_query (str): The title or part of the title of the paper.
        - config (dict): A dictionary with keys 'apikey' and 'insttoken'.
        - use_scopus (bool): Whether to use Scopus (True) or ScienceDirect (False) for the search.
        - limit_results (int): Optional limit on the number of results to fetch. If None, fetch all.
        """
        self.config = {
            "apikey": api_key,
            "insttoken": None
        }

        logging.debug("Initializing ElsevierPaperFetcher")
        self.title_query = title_query
        self.document: Optional[Dict[str, Any]] = None
        self.limit_results = limit_results  # Set the limit on number of results

        # Initialize the Elsevier client using the provided configuration dictionary.
        logging.debug("Initializing ElsClient with provided API key and insttoken")
        self.client = ElsClient(self.config['apikey'])
        if not self.config['insttoken']:
            self.client.inst_token = None
            logging.warning("No insttoken provided, proceeding without it.")
        else:
            self.client.inst_token = self.config['insttoken']
        
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
            metadata_list = [self.extract_metadata(entry) for entry in all_results]

            logging.info(f"Elsevier: Extracted DOIs: {doi_list}")
            logging.info(f"Elsevier: Extracted Full Text URLs: {full_text_urls}")

            return doi_list, full_text_urls, metadata_list
        else:
            logging.warning("No document found matching the title query.")
            return [], [], []

        
    def extract_full_text_urls(self, results: list) -> list:
        """
        Extracts the full-text URLs from the 'link' field where @ref='full-text'.
        """
        full_text_urls = []
        for entry in results:
            # Look for the 'link' field and extract the full-text URL if @ref='full-text'
            for link in entry.get("link", []):
                if link.get("@href") == "full-text":
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


    def extract_metadata(self, entry: dict) -> Dict[str, Any]:
        return {
            "title": entry.get("dc:title", "Title not available"),
            "doi": entry.get("prism:doi", "DOI not available"),
            "authors": entry.get("dc:creator", "Authors not available"),
            "published_date": entry.get("prism:coverDate", "Publication date not available"),
            "url": entry.get("prism:url", "URL not available")
        }


    def fetch_full_document(self, doi: str = None, uri: str = None) -> Optional[str]:
        """
        Fetches the full document using either DOI or URI.
        It first attempts to fetch using the DOI; if that fails (returns None),
        and if a URI is provided, it then tries fetching using the URI.
        Returns the full text (as a string) if available; otherwise, None.
        """
        result = None
        if doi:
            logging.debug(f"Fetching full document using DOI: {doi}")
            try:
                full_doc = FullDoc(doi=doi)
                if full_doc.read(self.client):
                    logging.info(f"Successfully fetched full document for DOI: {doi}")
                    doc_data = full_doc.data
                    # Check if 'originalText' exists and is non-empty
                    if "originalText" in doc_data and doc_data["originalText"].strip():
                        result = doc_data["originalText"]
                        result = filter_unwanted(result)
                    else:
                        logging.error(f"Full text for DOI {doi} is empty or missing; skipping this document.")
                        result = None
                else:
                    logging.warning(f"Failed to fetch full document for DOI: {doi}")
            except Exception as e:
                logging.error(f"Error fetching full document for DOI {doi}: {e}")

        if result is None and uri:
            logging.debug(f"DOI search failed; fetching full document using URI: {uri}")
            try:
                full_doc = FullDoc(uri=uri)
                if full_doc.read(self.client):
                    logging.info(f"Successfully fetched full document for URI: {uri}")
                    doc_data = full_doc.data
                    if "originalText" in doc_data and doc_data["originalText"].strip():
                        result = doc_data["originalText"]
                        result = filter_unwanted(result)
                    else:
                        logging.error(f"Full text for URI {uri} is empty or missing; skipping this document.")
                        result = None
                else:
                    logging.warning(f"Failed to fetch full document for URI: {uri}")
            except Exception as e:
                logging.error(f"Error fetching full document for URI {uri}: {e}")

        return result


# Example usage:
if __name__ == "__main__":
    logging.debug("Starting ElsevierPaperFetcher example.")
    
    
    # Initialize the fetcher with a title query and the config dictionary.
    fetcher = ElsevierPaperFetcher("Quantum algorithms", limit_results=5)  # Set a small limit
    doi_list, full_text_urls, metadata_list = fetcher.fetch_paper()

    logging.info(f"DOIs Extracted: {doi_list}")
    logging.info(f"Full Text URLs Extracted: {full_text_urls}")

    # For each entry, attempt to fetch the full document using both DOI and URI.
    for i in range(len(doi_list)):
        doi = doi_list[i]
        uri = full_text_urls[i] if i < len(full_text_urls) else None
        document_text = fetcher.fetch_full_document(doi=doi, uri=uri)
        # Use the metadata_list to get the title for naming the file.
        title = metadata_list[i]["title"] if i < len(metadata_list) else f"document_{i}"
        if document_text:
            write_document_to_file(title, document_text, directory="temp")
        else:
            logging.info(f"No full document data fetched for entry {i} (DOI: {doi}).")
