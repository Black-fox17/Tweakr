import json
from typing import Optional, Dict, Any
from elsapy.elsclient import ElsClient
from elsapy.elssearch import ElsSearch

class ElsevierPaperFetcher:
    def __init__(self, title_query: str, config: Dict[str, str], use_scopus: bool = True):
        """
        Initializes the fetcher with a title query.
        
        Parameters:
        - title_query (str): The title or a part of the title of the paper.
        - config (dict): A dictionary with keys 'apikey' and 'insttoken'.
        - use_scopus (bool): Whether to use Scopus (True) or ScienceDirect (False) for the search.
        """
        self.title_query = title_query
        self.document: Optional[Dict[str, Any]] = None
        
        # Initialize the Elsevier client using the provided configuration dictionary.
        self.client = ElsClient(config['apikey'])
        self.client.inst_token = config['insttoken']
        
        # Set search type.
        self.search_type = 'scopus' if use_scopus else 'sciencedirect'
        self.top_k = 1

    def fetch_paper(self):
        """
        Searches for the paper matching the title query and loads its metadata.
        """
        # Construct a query using the title. (Adjust the query format as needed.)
        query = f"TITLE({self.title_query})"
        search = ElsSearch(query, self.search_type)
        search.execute(self.client, get_all=True)
        if search.results and len(search.results) > 0:
            # We'll use the first result.
            self.document = search.results[0]
            # For debugging, print the title from the returned metadata (if available)
            title = self.get_title()
            print(f"Loaded document: {title}")
        else:
            print("No document found matching the title query.")

    def get_title(self) -> Optional[str]:
        """
        Returns the title of the fetched paper.
        """
        if self.document:
            # Scopus responses often use 'dc:title'
            return self.document.get("dc:title")
        return None

    def get_authors(self) -> Optional[str]:
        """
        Returns the authors of the fetched paper.
        """
        if self.document:
            # Authors may be stored under 'dc:creator'
            return self.document.get("dc:creator")
        return None

    def get_published_date(self) -> Optional[str]:
        """
        Returns the published date of the fetched paper.
        """
        if self.document:
            # For Scopus, the cover date might be under 'prism:coverDate'
            return self.document.get("prism:coverDate")
        return None

    def get_summary(self) -> Optional[str]:
        """
        Returns the summary (abstract) of the fetched paper.
        """
        if self.document:
            # Often the abstract is in 'dc:description' or a similar field.
            return self.document.get("dc:description")
        return None

    def get_links(self) -> Optional[str]:
        """
        Returns a primary link (URL) for the fetched paper.
        """
        if self.document:
            # Elsevier documents may provide a URL in a field like 'link'
            # This is an example; adjust according to the actual response.
            return self.document.get("link")
        return None

    def get_content(self) -> Optional[str]:
        """
        Returns the full content of the paper if available.
        (Often, full text is not directly available via the search API.)
        """
        if self.document:
            # Placeholder: if your document object contains full text, return it.
            return self.document.get("full_text")
        return None

# Example usage:
if __name__ == "__main__":
    # Instantiate the fetcher with a sample title query.
    fetcher = ElsevierPaperFetcher("Quantum algorithms")
    fetcher.fetch_paper()
    print("Title:", fetcher.get_title())
    print("Authors:", fetcher.get_authors())
    print("Published Date:", fetcher.get_published_date())
    print("Summary:", fetcher.get_summary())
    print("Link:", fetcher.get_links())
