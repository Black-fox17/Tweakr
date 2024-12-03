import os
import arxiv
import re
from arxiv import Client, Search, SortCriterion

class ArxivPaperDownloader:
    def __init__(self, query, max_results=10, download_dir='./store'):
        """
        Initializes the downloader with the search query, maximum number of results,
        and the directory where PDFs will be saved.

        Parameters:
        - query (str): The search term to query arXiv.
        - max_results (int): The maximum number of papers to retrieve.
        - download_dir (str): The directory path where PDFs will be stored.
        """
        self.query = query
        self.max_results = max_results
        self.download_dir = download_dir
        self.client = Client()

        # Ensure the target directory exists; create it if it doesn't
        os.makedirs(self.download_dir, exist_ok=True)

    def sanitize_filename(self, title):
        """
        Sanitizes the paper title to create a valid filename by replacing
        invalid characters with underscores.

        Parameters:
        - title (str): The title of the paper.

        Returns:
        - str: A sanitized string suitable for use as a filename.
        """
        # Replace any character that is not alphanumeric, whitespace, dot, or hyphen with an underscore
        return re.sub(r'[^\w\s.-]', '_', title)

    def download_papers(self):
        """
        Searches for papers matching the query and downloads their PDFs to the specified directory.

        Returns:
        - list: A list of dictionaries containing details of downloaded papers.
        """
        # Create a search object with the specified query and parameters
        search = Search(
            query=self.query,
            max_results=self.max_results,
            sort_by=SortCriterion.SubmittedDate
        )

        downloaded_papers = []  # List to store metadata of the downloaded papers
        # Iterate over the search results
        for result in self.client.results(search):
            print(f"Downloading: {result.title}")
            # Sanitize the title to create a valid filename
            sanitized_title = self.sanitize_filename(result.title)
            filename = f"{sanitized_title}.pdf"
            filepath = os.path.join(self.download_dir, filename)
            # Download the PDF to the specified directory with the sanitized filename
            result.download_pdf(dirpath=self.download_dir, filename=filename)
            # Append paper metadata and file path to the list
            downloaded_papers.append({
                'title': result.title,
                'authors': [author.name for author in result.authors],
                'published_date': result.published,
                'pdf_path': filepath
            })

        print(f"Downloaded {len(downloaded_papers)} papers.")
        return downloaded_papers

# Example usage:
# if __name__ == "__main__":
#     # Initialize the downloader with the desired query, number of results, and download directory
#     downloader = ArxivPaperDownloader(query="quantum", max_results=10, download_dir='./store')
#     # Download the papers and retrieve the list of downloaded paper details
#     downloaded_papers = downloader.download_papers()
#     # Print the titles and paths of the downloaded papers
#     for paper in downloaded_papers:
#         print(f"Title: {paper['title']}")
#         print(f"Authors: {paper['authors']}")
#         print(f"Published date: {paper['published_date']}")
#         print(f"PDF Path: {paper['pdf_path']}")
