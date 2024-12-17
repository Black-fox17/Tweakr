import os
from docx import Document
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from app.core.references_generator import ReferenceGenerator



import os
import spacy
import numpy as np
from docx import Document
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from dataclasses import dataclass

# Assuming you've installed spacy model:
# python -m spacy download en_core_web_sm
nlp = spacy.load("en_core_web_sm")

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers

@dataclass
class PaperMetadata:
    title: str
    authors: List[str]
    year: str
    category: str

class InTextCitationFormatter:
    """
    Formats in-text citations according to APA style for this example.
    """
    def format_citation(self, paper_meta: PaperMetadata) -> str:
        # APA in-text: (AuthorLastName, Year)
        # If multiple authors: (Author1 et al., Year)
        authors = paper_meta.authors
        year = paper_meta.year
        if not authors:
            return f"(Unknown, {year})"

        author_lastnames = [a.split()[-1] for a in authors]
        if len(author_lastnames) == 1:
            citation = f"({author_lastnames[0]}, {year})"
        elif len(author_lastnames) == 2:
            citation = f"({author_lastnames[0]} & {author_lastnames[1]}, {year})"
        else:
            citation = f"({author_lastnames[0]} et al., {year})"
        return citation

class SemanticCitationInserter:
    """
    Uses the vectorstore to find semantically related papers for each sentence in a document
    and inserts in-text citations.
    """
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str, threshold: float = 0.75):
        # Embedding model for sentences
        self.embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        # Initialize vector store
        from pymongo import MongoClient
        self.mongo_client = MongoClient(mongo_uri)
        db = self.mongo_client[db_name]
        collection = db[collection_name]
        
        self.vector_store = MongoDBAtlasVectorSearch(
            collection=collection,
            embedding=self.embedding_model,
            index_name=f"{collection_name}_index"
        )
        
        self.threshold = threshold
        self.citation_formatter = InTextCitationFormatter()

    def embed_sentence(self, sentence: str) -> np.ndarray:
        # The embeddings returned by `GoogleGenerativeAIEmbeddings.embed_query` are lists of floats
        return np.array(self.embedding_model.embed_query(sentence), dtype=float)

    def find_relevant_papers(self, sentence_embedding: np.ndarray, top_k=5) -> List[dict]:
        """
        Query the vectorstore with the sentence embedding to find relevant papers.
        The returned docs from vectorstore are `Document` objects with `.page_content` and `.metadata`.
        """
        # Convert embedding to list since similarity_search_by_vector might require it
        embedding_list = sentence_embedding.tolist()
        
        # Perform similarity search
        # similarity_search_by_vector method takes a vector and returns top_k documents
        results = self.vector_store.similarity_search_by_vector(embedding_list, k=top_k)
        
        # Filter by a similarity threshold if needed (if vector store returns scores)
        # Note: `MongoDBAtlasVectorSearch`'s `similarity_search_by_vector` method returns documents,
        # but doesn't directly return scores. If you need scores, you might have to modify the store or 
        # store them in metadata. For now, we assume all results are good candidates.
        return results

    def get_paper_metadata_from_postgres(self, title: str) -> PaperMetadata:
        """
        Retrieve full metadata from Postgres using the paper's title.
        """
        with get_session_with_ctx_manager() as session:
            paper = session.query(Papers).filter(Papers.title == title).first()
            if not paper:
                return PaperMetadata(title=title, authors=[], year="n.d.", category="")

            # Parse authors
            # Assuming authors stored as a comma-separated string or JSON list
            authors = []
            if paper.authors:
                # Try parsing authors (handle JSON or comma-separated)
                if paper.authors.strip().startswith("["):
                    # JSON list
                    import json
                    authors = json.loads(paper.authors)
                else:
                    # Comma separated
                    authors = [a.strip() for a in paper.authors.split(",")]

            year = "n.d."
            if paper.pub_date:
                year = str(paper.pub_date.year)
            
            return PaperMetadata(title=paper.title, authors=authors, year=year, category=paper.category)

    def process_document(self, input_doc_path: str, output_doc_path: str):
        doc = Document(input_doc_path)
        
        for para in doc.paragraphs:
            sentences = list(nlp(para.text).sents)
            new_para_text = ""
            
            for sent in sentences:
                sentence_text = sent.text.strip()
                if not sentence_text:
                    continue

                # Embed the sentence
                sentence_embedding = self.embed_sentence(sentence_text)
                
                # Find relevant papers via vector store
                relevant_paper_docs = self.find_relevant_papers(sentence_embedding, top_k=3)

                if relevant_paper_docs:
                    # For demonstration, we will cite all returned papers
                    citation_texts = []
                    for paper_doc in relevant_paper_docs:
                        # paper_doc.metadata should contain at least 'title'
                        paper_title = paper_doc.metadata.get("title")
                        if paper_title:
                            # Fetch full metadata from Postgres
                            paper_meta = self.get_paper_metadata_from_postgres(paper_title)
                            citation_text = self.citation_formatter.format_citation(paper_meta)
                            citation_texts.append(citation_text)

                    if citation_texts:
                        combined_citation = " ".join(citation_texts)
                        sentence_text = f"{sentence_text} {combined_citation}"

                # Reconstruct paragraph text
                if new_para_text:
                    new_para_text += " " + sentence_text
                else:
                    new_para_text = sentence_text

            para.text = new_para_text

        doc.save(output_doc_path)
        print(f"Document saved with in-text citations at {output_doc_path}")


if __name__ == "__main__":
    # You would replace these with your actual Mongo and DB details
    MONGO_URI = os.getenv("MONGO_DATABASE_URL")
    DB_NAME = "tweakr_papers_store"
    COLLECTION_NAME = "your_collection_name"  # The collection where you stored vector embeddings

    inserter = SemanticCitationInserter(
        mongo_uri=MONGO_URI,
        db_name=DB_NAME,
        collection_name=COLLECTION_NAME,
        threshold=0.75
    )

    input_doc = "/path/to/your/input_draft.docx"
    output_doc = "/path/to/output_draft_with_citations.docx"
    inserter.process_document(input_doc, output_doc)
