import logging
import requests
import xml.etree.ElementTree as ET


from datapipeline.core.constants import SPRINGER_API_KEY

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SpringerPaperFetcher:
    def __init__(self, query: str, api_key: str = SPRINGER_API_KEY, base_url: str = "https://api.springernature.com/openaccess/jats"):
        """
        Initializes the fetcher.
        
        Parameters:
        - query (str): The search query (e.g. "quantum energy")
        - api_key (str): Your Springer API key.
        - base_url (str): The base URL for the Springer JATS API.
        """
        self.query = query
        self.api_key = api_key
        self.base_url = base_url

    def _get_all_text(self, elem: ET.Element) -> str:
        """
        Recursively extracts and concatenates all text from an element.
        """
        texts = []
        if elem.text:
            texts.append(elem.text)
        for child in elem:
            texts.append(self._get_all_text(child))
            if child.tail:
                texts.append(child.tail)
        return "".join(texts)

    def _parse_article_info_from_element(self, article: ET.Element) -> dict:
        """
        Given an <article> element, extracts the following:
          - title
          - authors
          - doi and URL
          - published date
          - body content (all text from <body>)
        Returns a dictionary with these keys.
        """
        info = {}

        # Extract title
        title_elem = article.find("front/article-meta/title-group/article-title")
        if title_elem is not None and title_elem.text:
            info["title"] = title_elem.text.strip()
        else:
            info["title"] = "Title not found"

        # Extract authors
        authors = []
        contrib_elems = article.findall("front/article-meta/contrib-group/contrib[@contrib-type='author']")
        for contrib in contrib_elems:
            name_elem = contrib.find("name")
            if name_elem is not None:
                given = name_elem.find("given-names")
                surname = name_elem.find("surname")
                author_name = ""
                if given is not None and given.text:
                    author_name += given.text.strip() + " "
                if surname is not None and surname.text:
                    author_name += surname.text.strip()
                if author_name:
                    authors.append(author_name)
        info["authors"] = ", ".join(authors) if authors else "Authors not found"

        # Extract DOI and construct URL
        doi_elem = article.find("front/article-meta/article-id[@pub-id-type='doi']")
        if doi_elem is not None and doi_elem.text:
            doi = doi_elem.text.strip()
            info["doi"] = doi
            info["url"] = f"https://doi.org/{doi}"
        else:
            info["doi"] = ""
            info["url"] = "URL not available"

        # Extract published date (using the electronic pub date)
        pub_date_elem = article.find("front/article-meta/pub-date[@publication-format='electronic']")
        if pub_date_elem is not None:
            year = pub_date_elem.find("year")
            month = pub_date_elem.find("month")
            day = pub_date_elem.find("day")
            parts = []
            if year is not None and year.text:
                parts.append(year.text.strip())
            if month is not None and month.text:
                parts.append(month.text.strip().zfill(2))
            if day is not None and day.text:
                parts.append(day.text.strip().zfill(2))
            info["published_date"] = "-".join(parts) if parts else "Published date not found"
        else:
            info["published_date"] = "Published date not found"

        # Extract body text content
        body_elem = article.find("body")
        if body_elem is not None:
            info["content"] = self._get_all_text(body_elem).strip()
        else:
            info["content"] = "No body content found"

        return info

    def parse_articles_info(self, xml_string: str) -> list:
        """
        Parses an XML string representing a Springer JATS response and extracts all article info
        from the <records> tag.
        
        Returns a list of dictionaries, one for each article.
        """
        articles_info = []
        try:
            root = ET.fromstring(xml_string)
        except ET.ParseError as e:
            logging.error(f"Error parsing XML: {e}")
            return articles_info

        # If the XML is wrapped in a <response> element, look for all <article> tags within <records>
        if root.tag.lower() == "response":
            article_elems = root.findall(".//records/article")
            if not article_elems:
                logging.error("No <article> elements found in the response.")
            for article in article_elems:
                info = self._parse_article_info_from_element(article)
                articles_info.append(info)
        else:
            # If the XML is already a single <article>, parse it.
            info = self._parse_article_info_from_element(root)
            articles_info.append(info)
        return articles_info

    def fetch_articles(self) -> list:
        """
        Fetches the XML from the Springer JATS API using the query parameters,
        then parses it to extract information for all articles in the <records> tag.
        
        Returns a list of article information dictionaries.
        """
        params = {
            "api_key": self.api_key,
            "q": self.query
        }
        try:
            response = requests.get(self.base_url, params=params)
            logging.debug(f"Request URL: {response.url}")
            if response.status_code == 200:
                xml_string = response.text
                logging.info("Successfully fetched XML from Springer API")
                return self.parse_articles_info(xml_string)
            else:
                logging.error(f"Error fetching articles: HTTP {response.status_code}")
                return []
        except Exception as e:
            logging.error(f"Exception during request: {e}")
            return []

# Example usage:
if __name__ == "__main__":
    # Replace with your actual API key and query parameters.
    query = "quantum energy"
    
    fetcher = SpringerPaperFetcher(query=query)
    articles_info = fetcher.fetch_articles()
    
    if articles_info:
        for idx, article in enumerate(articles_info, start=1):
            logging.info(f"Article {idx}:")
            logging.info(f"  Title: {article.get('title')}")
            logging.info(f"  Authors: {article.get('authors')}")
            logging.info(f"  URL: {article.get('url')}")
            logging.info(f"  Published Date: {article.get('published_date')}")
            # Print only the first 300 characters of the content
            content_preview = article.get("content", "")[:300]
            logging.info(f"  Content (first 300 chars): {content_preview}\n")
    else:
        logging.error("No articles information could be fetched.")
