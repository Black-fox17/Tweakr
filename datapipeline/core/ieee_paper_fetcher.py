import requests
from bs4 import BeautifulSoup
from typing import Optional
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

class IEEEPaperFetcher:
    """Fetches papers from IEEE Xplore."""
    
    def __init__(self):
        self.base_url = "https://ieeexplore.ieee.org"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_paper(self, doi: str) -> Paper:
        """Fetch paper metadata and PDF content from IEEE Xplore."""
        url = f"{self.base_url}/document/{doi}"
        response = self.session.get(url)
        
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
        title_elem = soup.find('h1', class_='document-title')
        metadata['title'] = title_elem.text.strip() if title_elem else ''
        
        # Extract authors
        author_elems = soup.find_all('span', class_='author')
        metadata['authors'] = [author.text.strip() for author in author_elems]
        
        # Extract abstract
        abstract_elem = soup.find('div', class_='abstract-text')
        metadata['abstract'] = abstract_elem.text.strip() if abstract_elem else ''
        
        return metadata

    def _get_pdf_url(self, soup: BeautifulSoup) -> str:
        """Extract PDF download URL from BeautifulSoup object."""
        pdf_link = soup.find('a', {'data-doc-type': 'PDF'})
        if not pdf_link or 'href' not in pdf_link.attrs:
            raise PDFNotAccessibleError("Could not find PDF download link")
        return f"{self.base_url}{pdf_link['href']}"

    def _download_pdf(self, pdf_url: str) -> bytes:
        """Download PDF content from URL."""
        response = self.session.get(pdf_url)
        if response.status_code != 200:
            raise PDFNotAccessibleError("Could not download PDF")
        return response.content
