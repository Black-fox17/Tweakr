# # from langchain_community.document_loaders import ArxivLoader

# # # Define your search query and parameters
# # query = "quantum"
# # max_results = 10

# # # Initialize the ArxivLoader with the specified query and parameters
# # loader = ArxivLoader(query=query, load_max_docs=max_results)

# # # Load the documents
# # documents = loader.load()

# # # Display information about the loaded documents
# # print(f"Loaded {len(documents)} documents.")
# # for doc in documents:
# #     print(f"Title: {doc.metadata.get('Title')}")
# #     print(f"Authors: {doc.metadata.get('Authors')}")
# #     print(f"Published: {doc.metadata.get('Published')}")
# #     print(f"Summary: {doc.metadata.get('Summary')}")
# #     print(f"Content: {doc.page_content[:10000]}...")  # Display the first 500 characters of the content
# #     print("\n" + "="*80 + "\n")


# from langchain_community.utilities import ArxivAPIWrapper
# from typing import List, Optional, Dict

# class ArxivPaperRetriever:
#     def __init__(self, query: str = "", max_results: int = 10):
#         """
#         Initializes the retriever with an optional search query and maximum number of results.

#         Parameters:
#         - query (str): The search term to query arXiv.
#         - max_results (int): The maximum number of papers to retrieve.
#         """
#         self.query = query
#         self.max_results = max_results
#         self.documents = []
#         self.arxiv = ArxivAPIWrapper(
#             top_k_results=self.max_results,
#             load_max_docs=self.max_results,
#             load_all_available_meta=True
#         )
#         self.arxiv.load("2018")

#     def search_papers(self):
#         """
#         Searches for papers matching the query and loads their content into Document objects.
#         """
#         if not self.query:
#             raise ValueError("Query must be provided to search papers.")
#         self.documents = self.arxiv.get_summaries_as_docs(self.query)
#         print(f"Loaded {len(self.documents)} documents.")

#     def get_titles(self) -> List[str]:
#         """
#         Returns a list of titles of the loaded papers.
#         """
#         return [doc.metadata.get('Title', 'No Title') for doc in self.documents]

#     def get_authors(self) -> List[List[str]]:
#         """
#         Returns a list of authors for each loaded paper.
#         """
#         return [doc.metadata.get('Authors', 'No Authors') for doc in self.documents]

#     def get_published_dates(self) -> List[str]:
#         """
#         Returns a list of published dates for each loaded paper.
#         """
#         return [doc.metadata.get('Published', 'No Date') for doc in self.documents]

#     def get_summaries(self) -> List[str]:
#         """
#         Returns a list of summaries for each loaded paper.
#         """
#         return [doc.metadata.get('Summary', 'No Summary') for doc in self.documents]

#     def get_contents(self) -> List[str]:
#         """
#         Returns a list of contents for each loaded paper.
#         """
#         return [doc.page_content for doc in self.documents]

#     def get_paper_by_title(self, title: str) -> Optional[Dict[str, str]]:
#         """
#         Retrieves the details of a paper by its title.

#         Parameters:
#         - title (str): The title of the paper to retrieve.

#         Returns:
#         - dict: A dictionary containing the paper's details, or None if not found.
#         """
#         for doc in self.documents:
#             if doc.metadata.get('Title', '').lower() == title.lower():
#                 return {
#                     'Title': doc.metadata.get('Title'),
#                     'Authors': doc.metadata.get('Authors'),
#                     'Published': doc.metadata.get('Published'),
#                     'Summary': doc.metadata.get('Summary'),
#                     'Content': doc.page_content
#                 }
#         return None

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
if __name__ == "__main__":
    paper_title = "Bit symmetry entails the symmetry of thequantum transition probability"
    fetcher = ArxivPaperFetcher(title_query=paper_title)
    fetcher.fetch_paper()
    print("Title:", fetcher.get_title())
    print("Authors:", fetcher.get_authors())
    print("Published Date:", fetcher.get_published_date())
    print("Summary:", fetcher.get_summary())
    print("Content:", fetcher.get_content())