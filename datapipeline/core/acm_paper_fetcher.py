import requests
from bs4 import BeautifulSoup
from typing import Optional, List
from dataclasses import dataclass

@dataclass
class Paper:
    doi: str
    title: str
    authors: list[str]
    abstract: str
    pdf_content: Optional[bytes] = None

class PDFNotAccessibleError(Exception):
    """Raised when PDF cannot be accessed or downloaded."""
    pass

class PaperNotFoundError(Exception):
    """Raised when paper cannot be found."""
    pass

class ACMPaperFetcher:
    """Fetches paper metadata and PDFs from the ACM Digital Library."""

    def __init__(self, query: str = "", max_results: int = 10):
        """Initialize the ACM paper fetcher."""
        self.session = requests.Session()
        self.base_url = "https://dl.acm.org"
        self.query = query
        self.max_results = max_results

    def fetch_papers(self) -> List[Paper]:
        """
        Search for papers matching the query and return their metadata.
        
        Returns:
            List of Paper objects containing metadata
        """
        search_url = f"{self.base_url}/action/doSearch"
        params = {
            "AllField": self.query,
            "pageSize": self.max_results
        }
        
        response = self.session.get(search_url, params=params)
        if response.status_code != 200:
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        papers = []
        
        for result in soup.find_all('div', class_='issue-item'):
            try:
                doi = result.find('a', class_='issue-item__doi').text.strip()
                title = result.find('h5', class_='issue-item__title').text.strip()
                authors = [author.text.strip() for author in result.find_all('span', class_='author-name')]
                abstract = result.find('div', class_='issue-item__abstract').text.strip()
                
                papers.append(Paper(
                    doi=doi,
                    title=title,
                    authors=authors,
                    abstract=abstract
                ))
            except (AttributeError, TypeError):
                continue
                
        return papers

    def fetch_paper(self, doi: str):
        """
        Fetch metadata and PDF for a paper from ACM Digital Library.
        
        Args:
            doi: DOI of the paper to fetch
            
        Returns:
            Paper object containing metadata and PDF content
            
        Raises:
            PaperNotFoundError: If paper cannot be found
            PDFNotAccessibleError: If PDF cannot be accessed
        """
        paper_url = f"{self.base_url}/doi/{doi}"
        response = self.session.get(paper_url)
        
        if response.status_code != 200:
            raise PaperNotFoundError(f"Could not find paper with DOI: {doi}")
            
        # Parse metadata from response
        soup = BeautifulSoup(response.text, 'html.parser')
        metadata = self._extract_metadata(soup)
        
        # Get PDF content
        pdf_url = self._get_pdf_url(soup)
        pdf_content = self._download_pdf(pdf_url)
        
        return Paper(
            doi=doi,
            title=metadata['title'],
            authors=metadata['authors'],
            abstract=metadata['abstract'],
            pdf_content=pdf_content
        )

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract paper metadata from BeautifulSoup object."""
        metadata = {}
        
        # Extract title
        title_elem = soup.find('h1', class_='citation__title')
        metadata['title'] = title_elem.text.strip() if title_elem else ''
        
        # Extract authors
        author_elems = soup.find_all('span', class_='author-name')
        metadata['authors'] = [author.text.strip() for author in author_elems]
        
        # Extract abstract
        abstract_elem = soup.find('div', class_='abstractSection')
        metadata['abstract'] = abstract_elem.text.strip() if abstract_elem else ''
        
        return metadata

    def _get_pdf_url(self, soup: BeautifulSoup) -> str:
        """Extract PDF download URL from BeautifulSoup object."""
        pdf_link = soup.find('a', {'title': 'PDF'})
        if not pdf_link or 'href' not in pdf_link.attrs:
            raise PDFNotAccessibleError("Could not find PDF download link")
        return f"{self.base_url}{pdf_link['href']}"

    def _download_pdf(self, pdf_url: str) -> bytes:
        """Download PDF content from URL."""
        response = self.session.get(pdf_url)
        if response.status_code != 200:
            raise PDFNotAccessibleError("Could not download PDF")
        return response.content
