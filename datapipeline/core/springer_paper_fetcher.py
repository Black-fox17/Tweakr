import logging
import requests
import xml.etree.ElementTree as ET

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SpringerPaperFetcher:
    def __init__(self, query: str, api_key: str, limit_results: Optional[int] = None):
        """
        Initializes the fetcher with a query and optional result limit.

        Parameters:
        - query (str): The query for the search.
        - api_key (str): API key for Springer API.
        - limit_results (int): Optional limit on the number of results to fetch. If None, fetch all.
        """
        self.query = query
        self.api_key = api_key
        self.limit_results = limit_results
        self.base_url = "https://api.springernature.com/openaccess/json"
        self.jats_url = "https://api.springernature.com/openaccess/jats"
        self.top_k = 10  # Number of results per page

    def fetch_metadata(self):
        """
        Fetch metadata for articles based on the query and extract relevant details.
        """
        logging.debug(f"Fetching metadata for query: {self.query}")

        url = f"{self.base_url}?api_key={self.api_key}&q={self.query}"
        all_results = []
        page = 1  # Start at the first page

        while True:
            logging.debug(f"Sending GET request to fetch metadata (page {page})")
            response = requests.get(f"{url}&s={page}")
            data = response.json()

            if 'records' in data:
                all_results.extend(data['records'])
                logging.debug(f"Fetched {len(data['records'])} results (Total fetched: {len(all_results)})")
            else:
                logging.warning("No records found.")
                break

            # Check if there's a next page and handle pagination
            if 'nextPage' in data:
                page += 1
            else:
                break

            # If the result limit is set and we've fetched that many, stop
            if self.limit_results and len(all_results) >= self.limit_results:
                logging.debug(f"Fetched the limited {self.limit_results} results.")
                break

        if all_results:
            logging.info(f"Total {len(all_results)} records fetched.")
            return all_results
        else:
            logging.warning("No metadata found matching the query.")
            return []

    def fetch_full_text(self, doi: str):
        """
        Given a DOI, fetch the full-text article content from Springer.
        """
        logging.debug(f"Fetching full-text content for DOI: {doi}")

        url = f"{self.jats_url}?api_key={self.api_key}&doi={doi}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                full_text_data = response.text  # Raw XML response from Springer
                return self.extract_full_text_url(full_text_data)
            else:
                logging.warning(f"Failed to fetch full text for DOI: {doi}")
                return None
        except Exception as e:
            logging.error(f"Error fetching full text for DOI {doi}: {e}")
            return None

    def extract_full_text_url(self, xml_data: str):
        """
        Extracts the full-text URL from the XML response.
        """
        try:
            # Parse the XML response
            root = ET.fromstring(xml_data)
            # Find all the full-text links
            full_text_links = []

            for article in root.findall(".//article"):
                for link in article.findall(".//link[@ref='full-text']"):
                    full_text_url = link.get("{http://www.w3.org/1999/xlink}href")
                    if full_text_url:
                        full_text_links.append(full_text_url)

            return full_text_links
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            return []

    def extract_metadata(self, articles: list):
        """
        Extract relevant metadata (title, DOI, authors, publication date) from the articles.
        """
        metadata_list = []
        for article in articles:
            title = article.get("title", "Title not available")
            doi = article.get("doi", "DOI not available")
            authors = self.extract_authors(article)
            publication_date = article.get("publicationDate", "Publication date not available")
            metadata = {
                "title": title,
                "doi": doi,
                "authors": authors,
                "publication_date": publication_date
            }
            metadata_list.append(metadata)
        return metadata_list

    def extract_authors(self, article):
        """
        Extracts authors from the article metadata.
        """
        authors = []
        for author in article.get("authors", []):
            author_name = f"{author.get('givenNames', '')} {author.get('surname', '')}"
            authors.append(author_name)
        return authors

    def fetch_articles(self):
        """
        Fetches articles metadata and full text for each article.
        """
        metadata = self.fetch_metadata()
        articles_metadata = self.extract_metadata(metadata)

        for article in articles_metadata:
            doi = article["doi"]
            if doi != "DOI not available":
                full_text = self.fetch_full_text(doi)
                if full_text:
                    logging.info(f"Full text URLs for {doi}: {full_text}")

        return articles_metadata


# Example usage:
if __name__ == "__main__":
    logging.debug("Starting SpringerPaperFetcher example.")

    # Define configuration as a dictionary.
    api_key = "YOUR_API_KEY"  # Replace with your API key from Springer
    query = "quantum energy"

    fetcher = SpringerPaperFetcher(query=query, api_key=api_key, limit_results=5)  # Set a small limit
    articles_metadata = fetcher.fetch_articles()

    logging.info(f"Fetched articles metadata: {articles_metadata}")
