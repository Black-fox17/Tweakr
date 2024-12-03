from langchain_community.utilities import ArxivAPIWrapper
from typing import Optional, Dict

class ArxivPaperFetcher:
    def __init__(self, title_query: str):
        """
        Initializes the fetcher with the title of the paper to query arXiv.

        Parameters:
        - title_query (str): The title or part of the title of the paper to query arXiv.
        """
        self.title_query = title_query
        self.document = None
        self.arxiv = ArxivAPIWrapper(
            arxiv_search=self.title_query,
            top_k_results=1,
            load_max_docs=1,
            load_all_available_meta=True
        )

    def fetch_paper(self):
        """
        Searches for the paper matching the title query and loads its content into a Document object.
        """
        documents = self.arxiv.load(self.title_query)
        if documents:
            self.document = documents[0]
            print(f"Loaded document: {self.document.metadata.get('Title')}")
        else:
            print("No document found matching the title query.")

    def get_title(self) -> Optional[str]:
        """
        Returns the title of the fetched paper.
        """
        return self.document.metadata.get('Title') if self.document else None

    def get_authors(self) -> Optional[str]:
        """
        Returns the authors of the fetched paper.
        """
        return self.document.metadata.get('Authors') if self.document else None

    def get_published_date(self) -> Optional[str]:
        """
        Returns the published date of the fetched paper.
        """
        return self.document.metadata.get('Published') if self.document else None

    def get_summary(self) -> Optional[str]:
        """
        Returns the summary of the fetched paper.
        """
        return self.document.metadata.get('Summary') if self.document else None

    def get_content(self) -> Optional[str]:
        """
        Returns the content of the fetched paper.
        """
        return self.document.page_content if self.document else None

# Example usage:
# if __name__ == "__main__":
#     paper_title = "Bit symmetry entails the symmetry of thequantum transition probability"
#     fetcher = ArxivPaperFetcher(title_query=paper_title)
#     fetcher.fetch_paper()
#     print("Title:", fetcher.get_title())
#     print("Authors:", fetcher.get_authors())
#     print("Published Date:", fetcher.get_published_date())
#     print("Summary:", fetcher.get_summary())
#     print("Content:", fetcher.get_content())