import os
from docx import Document
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from app.core.references_generator import ReferenceGenerator
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from datapipeline.core.utils import embeddings 
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from app.core.headings import headers  # Import the headings
import spacy
import logging

# Load SpaCy model for sentence segmentation
nlp = spacy.load("en_core_web_sm")

# Setup logging
logging.basicConfig(level=logging.INFO)


# class InTextCitationProcessor:
#     def __init__(self, style="APA", collection_name="general", threshold=0.75, top_k=5):
#         """
#         Initialize the citation processor.

#         Parameters:
#         - style (str): Citation style (APA, MLA, Chicago).
#         - collection_name (str): MongoDB collection for vector searches.
#         - threshold (float): Minimum similarity threshold for semantic matching.
#         - top_k (int): Number of top relevant documents to retrieve.
#         """
#         self.style = style
#         self.reference_generator = ReferenceGenerator(style=style)
#         self.mongo_manager = MongoDBVectorStoreManager(
#             connection_string=MONGODB_ATLAS_CLUSTER_URI,
#             db_name=MONGO_DB_NAME
#         )
#         self.collection_name = collection_name
#         self.threshold = threshold
#         self.top_k = top_k
#         self.headers = headers  # Load predefined headings

#     def read_file_content(self, file_path: str) -> str:
#         """
#         Read file content from .txt or .docx files.
#         """
#         if not os.path.exists(file_path):
#             raise FileNotFoundError(f"File '{file_path}' does not exist.")

#         ext = os.path.splitext(file_path)[1].lower()
#         if ext == ".txt":
#             with open(file_path, "r", encoding="utf-8") as f:
#                 return f.read()
#         elif ext == ".docx":
#             doc = Document(file_path)
#             return "\n".join([p.text for p in doc.paragraphs])
#         else:
#             raise ValueError("Unsupported file type. Only .txt and .docx are supported.")

#     def fetch_metadata_from_db(self, title: str) -> Dict:
#         """
#         Fetch metadata (authors, published_date) from PostgreSQL by title.

#         Parameters:
#         - title (str): Title of the paper to look up.

#         Returns:
#         - dict: A dictionary containing authors and published_date.
#         """
#         if not isinstance(title, str) or not title.strip():
#             logging.error(f"Invalid title for database fetch: {title}")
#             return {"authors": ["Unknown"], "published_date": "n.d."}

#         logging.info(f"Fetching metadata from DB for title: {title}")
#         with get_session_with_ctx_manager() as session:
#             paper = session.query(Papers).filter(Papers.title == title).first()
#             if not paper:
#                 logging.warning(f"Paper with title '{title}' not found in the database.")
#                 return {"authors": ["Unknown"], "published_date": "n.d."}

#             try:
#                 # Parse authors
#                 authors = []
#                 if paper.authors:
#                     if paper.authors.strip().startswith("["):
#                         authors = json.loads(paper.authors)
#                     else:
#                         authors = [a.strip() for a in paper.authors.split(",")]

#                 # Parse publication year
#                 published_date = "n.d."
#                 if paper.pub_date and isinstance(paper.pub_date, (datetime, str)):
#                     published_date = str(paper.pub_date.year)

#                 metadata = {
#                     "authors": authors if authors else ["Unknown"],
#                     "published_date": published_date or "n.d."
#                 }
#                 logging.debug(f"Fetched metadata: {metadata}")
#                 return metadata

#             except Exception as e:
#                 logging.error(f"Error fetching metadata for title '{title}': {e}")
#                 return {"authors": ["Unknown"], "published_date": "n.d."}


#     def embed_sentence(self, sentence: str) -> List[float]:
#         """
#         Create an embedding for a sentence using the embeddings utility.
#         """
#         if not isinstance(sentence, str) or not sentence.strip():
#             logging.error(f"Invalid sentence for embedding: {sentence}")
#             raise ValueError(f"Invalid sentence for embedding: {sentence}")
#         try:
#             logging.debug(f"Creating embedding for sentence: {sentence}")
#             return embeddings.embed_query(sentence)
#         except Exception as e:
#             logging.error(f"Error generating embedding for sentence: {sentence}, error: {e}")
#             raise


#     def find_relevant_papers(self, sentence: str) -> List[Dict]:
#         """
#         Retrieve semantically relevant papers for a sentence.
#         """
#         if not isinstance(sentence, str) or not sentence.strip():
#             logging.warning(f"Skipping empty or invalid sentence: {sentence}")
#             return []

#         try:
#             # Directly pass the sentence as the query
#             results = self.mongo_manager.similarity_search_by_text(
#                 collection_name=self.collection_name, query=sentence, k=self.top_k
#             )
#             logging.debug(f"Found {len(results)} relevant papers for sentence: {sentence}")
#             return results
#         except Exception as e:
#             logging.error(f"Error during similarity search for sentence: {sentence}, error: {e}")
#             return []



#     def format_citation(self, authors: List[str], year: str) -> str:
#         """
#         Format in-text citation based on the specified style.
#         """
#         if not authors:
#             authors = ["Unknown"]
#         if not year or not isinstance(year, str):
#             year = "n.d."

#         if self.style == "APA":
#             return f"({', '.join(authors)}, {year})"
#         elif self.style == "MLA":
#             return f"({authors[0]} et al., {year})" if len(authors) > 1 else f"({authors[0]}, {year})"
#         elif self.style == "Chicago":
#             return f"({', '.join(authors)}, {year})"
#         else:
#             raise ValueError(f"Unsupported citation style: {self.style}")


#     def is_heading(self, paragraph: str) -> bool:
#         """
#         Check if a paragraph is a heading to be skipped.
#         """
#         is_heading_detected = paragraph.strip() in self.headers
#         if is_heading_detected:
#             logging.info(f"Detected heading: {paragraph.strip()}")
#         return is_heading_detected


#     def process_sentences(self, input_path: str, output_path: str):
#         """
#         Process each sentence in the document for in-text citations.

#         Parameters:
#         - input_path (str): Path to the input document.
#         - output_path (str): Path to save the updated document.
#         """
#         logging.info(f"Starting sentence-level processing for file: {input_path}")
#         doc = Document(input_path)
#         updated_paragraphs = []

#         for para_idx, para in enumerate(doc.paragraphs):
#             paragraph_text = para.text.strip()
#             logging.debug(f"Processing paragraph {para_idx + 1}: {paragraph_text}")

#             # Skip empty paragraphs
#             if not paragraph_text:
#                 logging.info(f"Skipping empty paragraph {para_idx + 1}")
#                 updated_paragraphs.append("")
#                 continue

#             # Skip headings
#             if self.is_heading(paragraph_text):
#                 logging.info(f"Skipping heading: {paragraph_text}")
#                 updated_paragraphs.append(paragraph_text)
#                 continue

#             # Process sentences in the paragraph
#             sentences = list(nlp(paragraph_text).sents)
#             processed_sentences = []

#             for sent_idx, sent in enumerate(sentences):
#                 sentence_text = sent.text.strip()
#                 logging.debug(f"Processing sentence {sent_idx + 1} in paragraph {para_idx + 1}: {sentence_text}")

#                 if not sentence_text:
#                     logging.info(f"Skipping empty sentence in paragraph {para_idx + 1}")
#                     continue

#                 # Perform similarity search and citation generation
#                 try:
#                     relevant_papers = self.find_relevant_papers(sentence_text)
#                     logging.debug(f"Found {len(relevant_papers)} relevant papers for sentence: {sentence_text}")
#                     citation_texts = []

#                     for paper_doc in relevant_papers:
#                         metadata = paper_doc.get("metadata", {})
#                         title = metadata.get("title")
#                         if not title:
#                             logging.error("Missing title in paper metadata. Skipping this paper.")
#                             continue

#                         db_metadata = self.fetch_metadata_from_db(title)
#                         authors = db_metadata.get("authors", ["Unknown"])
#                         year = db_metadata.get("published_date", "n.d.")
#                         logging.debug(f"Metadata for citation: title={title}, authors={authors}, year={year}")

#                         citation = self.format_citation(authors, year)
#                         citation_texts.append(citation)

#                     if citation_texts:
#                         sentence_text += " " + " ".join(citation_texts)

#                 except Exception as e:
#                     logging.error(f"Error processing sentence: {sentence_text}, error: {e}")
#                     continue

#                 processed_sentences.append(sentence_text)

#             # Combine processed sentences back into a paragraph
#             updated_paragraphs.append(" ".join(processed_sentences))

#         # Save updated content back to the document
#         for idx, updated_text in enumerate(updated_paragraphs):
#             doc.paragraphs[idx].text = updated_text

#         doc.save(output_path)
#         logging.info(f"Processed document saved at: {output_path}")



#     def process_paragraphs(self, input_path: str, output_path: str):
#         """
#         Process entire paragraphs for in-text citations.

#         Parameters:
#         - input_path (str): Path to the input document.
#         - output_path (str): Path to save the updated document.
#         """
#         logging.info(f"Starting paragraph-level processing for file: {input_path}")
#         doc = Document(input_path)

#         for para_idx, para in enumerate(doc.paragraphs):
#             paragraph_text = para.text.strip()
#             logging.debug(f"Processing paragraph {para_idx + 1}: {paragraph_text}")

#             if not paragraph_text:
#                 logging.info(f"Skipping empty paragraph {para_idx + 1}")
#                 continue

#             if self.is_heading(paragraph_text):
#                 logging.info(f"Detected heading: {paragraph_text}")
#                 logging.info(f"Skipping heading: {paragraph_text}")
#                 continue

#             # Reuse `process_sentences` logic to handle paragraph-level citations
#             sentences = list(nlp(paragraph_text).sents)
#             new_para_text = ""

#             for sent_idx, sent in enumerate(sentences):
#                 sentence_text = sent.text.strip()
#                 logging.debug(f"Processing sentence {sent_idx + 1} in paragraph {para_idx + 1}: {sentence_text}")
#                 # Add citation processing logic here
#                 ...

#             para.text = new_para_text

#         doc.save(output_path)
#         logging.info(f"Processed document saved at: {output_path}")



#     def process_document(self, input_path: str, output_path: str):
#         """
#         Add in-text citations to the document and save the modified content.

#         Parameters:
#         - input_path (str): Path to the input document.
#         - output_path (str): Path to save the document with citations.
#         """
#         logging.info(f"Starting document processing for file: {input_path}")
#         doc = Document(input_path)

#         for para_idx, para in enumerate(doc.paragraphs):
#             paragraph_text = para.text.strip()
#             logging.debug(f"Processing paragraph {para_idx + 1}: {paragraph_text}")

#             if not paragraph_text:
#                 logging.info(f"Skipping empty paragraph {para_idx + 1}")
#                 continue

#             if self.is_heading(paragraph_text):
#                 logging.info(f"Skipping heading: {paragraph_text}")
#                 continue

#             logging.debug(f"Processing body paragraph {para_idx + 1}")
#             sentences = list(nlp(paragraph_text).sents)
#             new_para_text = ""

#             for sent_idx, sent in enumerate(sentences):
#                 sentence_text = sent.text.strip()
#                 logging.debug(f"Processing sentence {sent_idx + 1} in paragraph {para_idx + 1}: {sentence_text}")

#                 if not sentence_text:
#                     logging.info(f"Skipping empty sentence in paragraph {para_idx + 1}")
#                     continue

#                 try:
#                     relevant_papers = self.find_relevant_papers(sentence_text)
#                     logging.debug(f"Found {len(relevant_papers)} relevant papers for sentence: {sentence_text}")
#                     citation_texts = []

#                     for paper_doc in relevant_papers:
#                         metadata = paper_doc.get("metadata", {})
#                         title = metadata.get("title")
#                         if not title:
#                             logging.error("Missing title in paper metadata. Skipping this paper.")
#                             continue

#                         db_metadata = self.fetch_metadata_from_db(title)
#                         authors = db_metadata.get("authors", ["Unknown"])
#                         year = db_metadata.get("published_date", "n.d.")
#                         logging.debug(f"Metadata for citation: title={title}, authors={authors}, year={year}")

#                         if authors:
#                             citation = self.format_citation(authors, year)
#                             citation_texts.append(citation)

#                     if citation_texts:
#                         sentence_text += " " + " ".join(citation_texts)

#                 except Exception as e:
#                     logging.error(f"Error processing sentence: {sentence_text}, error: {e}")
#                     continue

#                 new_para_text += (" " if new_para_text else "") + sentence_text

#             if new_para_text:
#                 logging.debug(f"Updated paragraph {para_idx + 1}: {new_para_text}")
#                 para.text = new_para_text

#         doc.save(output_path)
#         logging.info(f"Processed document saved at: {output_path}")


class InTextCitationProcessor:
    def __init__(self, style="APA", collection_name="general", threshold=0.0, top_k=5):
        """
        Initialize the citation processor.

        Parameters:
        - style (str): Citation style (APA, MLA, Chicago).
        - collection_name (str): MongoDB collection for vector searches.
        - threshold (float): Minimum similarity threshold for semantic matching.
        - top_k (int): Number of top relevant documents to retrieve.
        """
        self.style = style
        self.reference_generator = ReferenceGenerator(style=style)
        self.mongo_manager = MongoDBVectorStoreManager(
            connection_string=MONGODB_ATLAS_CLUSTER_URI,
            db_name=MONGO_DB_NAME
        )
        self.collection_name = collection_name
        self.threshold = threshold
        self.top_k = top_k
        self.headers = headers  # Load predefined headings

        # Load SpaCy model for sentence segmentation
        self.nlp = spacy.load("en_core_web_sm")

    def fetch_metadata_from_db(self, title: str) -> Dict:
        """
        Fetch metadata (authors, published_date) from PostgreSQL by title.
        """
        if not isinstance(title, str) or not title.strip():
            logging.error(f"Invalid title for database fetch: '{title}'")
            return {"authors": ["Unknown"], "published_date": "n.d."}

        logging.info(f"Fetching metadata from DB for title: '{title}'")
        with get_session_with_ctx_manager() as session:
            paper = session.query(Papers).filter(Papers.title == title).first()
            if not paper:
                logging.warning(f"Paper with title '{title}' not found in the database.")
                return {"authors": ["Unknown"], "published_date": "n.d."}

            try:
                # Parse authors
                authors = []
                if getattr(paper, "authors", None):
                    if paper.authors.strip().startswith("["):
                        authors = json.loads(paper.authors)
                    else:
                        authors = [a.strip() for a in paper.authors.split(",")]

                # Parse publication year
                published_date = "n.d."
                if getattr(paper, "pub_date", None):
                    if isinstance(paper.pub_date, datetime):
                        published_date = str(paper.pub_date.year)
                    else:
                        # If it's a string (e.g. "2020-05-06" or just "2020")
                        published_date = paper.pub_date[:4]

                metadata = {
                    "authors": authors if authors else ["Unknown"],
                    "published_date": published_date or "n.d."
                }
                logging.debug(f"Fetched metadata from DB: {metadata}")
                return metadata

            except Exception as e:
                logging.error(f"Error fetching metadata for title '{title}': {e}")
                return {"authors": ["Unknown"], "published_date": "n.d."}

    def is_heading(self, paragraph: str) -> bool:
        """
        Check if a paragraph is a heading to be skipped.
        """
        candidate = paragraph.strip()
        is_heading_detected = candidate in self.headers
        if is_heading_detected:
            logging.info(f"Detected heading: '{candidate}'")
        return is_heading_detected

    def format_citation(self, authors: List[str], year: str) -> str:
        """
        Format in-text citation based on the specified style.
        """
        if not authors:
            authors = ["Unknown"]
        if not year or not isinstance(year, str):
            year = "n.d."

        if self.style == "APA":
            return f"({', '.join(authors)}, {year})"
        elif self.style == "MLA":
            if len(authors) > 1:
                return f"({authors[0]} et al., {year})"
            else:
                return f"({authors[0]}, {year})"
        elif self.style == "Chicago":
            return f"({', '.join(authors)}, {year})"
        else:
            raise ValueError(f"Unsupported citation style: {self.style}")

    def find_relevant_papers(self, sentence: str):
        """
        Retrieve semantically relevant papers for a sentence using similarity search,
        then filter them by the threshold.
        """
        if not isinstance(sentence, str) or not sentence.strip():
            logging.warning(f"Skipping empty or invalid sentence: '{sentence}'")
            return []

        try:
            results = self.mongo_manager.semantic_search(
                collection_name=self.collection_name,
                query=sentence,
                k=self.top_k
            )
            logging.debug(f"Raw similarity search returned {len(results)} documents for sentence: '{sentence}'")

            # Filter by threshold
            filtered_results = []
            for doc in results:
                score = doc.metadata.get("score", 0.0)
                if score >= self.threshold:
                    filtered_results.append(doc)
                else:
                    logging.debug(
                        f"Document '{doc.metadata.get('title', 'Unknown')}' "
                        f"filtered out with score {score:.2f} < threshold {self.threshold:.2f}"
                    )

            if not filtered_results:
                logging.info(
                    f"No documents found above threshold={self.threshold} for sentence: '{sentence}'"
                )
            else:
                logging.info(
                    f"Found {len(filtered_results)} documents above threshold={self.threshold} for sentence: '{sentence}'"
                )

            return filtered_results

        except Exception as e:
            logging.error(f"Error during similarity search for sentence '{sentence}': {e}")
            return []

    def process_sentences(self, input_path: str, output_path: str):
        """
        Process each sentence in the document for in-text citations.
        """
        logging.info(f"Starting sentence-level processing for file: '{input_path}'")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        doc = Document(input_path)
        updated_paragraphs = []

        for para_idx, para in enumerate(doc.paragraphs, start=1):
            paragraph_text = para.text.strip()
            logging.debug(f"Paragraph {para_idx} original text: '{paragraph_text}'")

            if not paragraph_text:
                logging.info(f"Skipping empty paragraph {para_idx}")
                updated_paragraphs.append("")
                continue

            # Check if this paragraph is recognized as a heading
            if self.is_heading(paragraph_text):
                logging.info(f"Skipping heading: '{paragraph_text}' in paragraph {para_idx}")
                updated_paragraphs.append(paragraph_text)
                continue

            # Tokenize paragraph into sentences
            sentences = list(self.nlp(paragraph_text).sents)
            processed_sentences = []

            for sent_idx, sent in enumerate(sentences, start=1):
                sentence_text = sent.text.strip()
                logging.debug(f"Processing sentence {sent_idx} in paragraph {para_idx}: '{sentence_text}'")

                if not sentence_text:
                    logging.info(f"Skipping empty sentence in paragraph {para_idx}")
                    continue

                try:
                    relevant_papers = self.find_relevant_papers(sentence_text)
                    if not relevant_papers:
                        processed_sentences.append(sentence_text)
                        continue

                    # Build citations from relevant papers
                    citation_texts = []
                    for paper_doc in relevant_papers:
                        metadata = paper_doc.get("metadata", {})
                        title = metadata.get("title")
                        if not title:
                            logging.error("Missing 'title' in paper metadata. Skipping this paper.")
                            continue

                        db_metadata = self.fetch_metadata_from_db(title)
                        authors = db_metadata.get("authors", ["Unknown"])
                        year = db_metadata.get("published_date", "n.d.")
                        logging.debug(
                            f"Formatting citation for doc with title='{title}', authors={authors}, year={year}"
                        )
                        citation = self.format_citation(authors, year)
                        citation_texts.append(citation)

                    # If we have any citations, append them
                    if citation_texts:
                        sentence_text += " " + " ".join(citation_texts)

                except Exception as e:
                    logging.error(f"Error processing sentence '{sentence_text}' in paragraph {para_idx}: {e}")
                    # Add the original sentence to keep doc consistent
                    processed_sentences.append(sentence_text)
                    continue

                processed_sentences.append(sentence_text)

            # Reconstruct the paragraph
            final_paragraph_text = " ".join(processed_sentences)
            updated_paragraphs.append(final_paragraph_text)

        # Save updated content back to the document
        for idx, updated_text in enumerate(updated_paragraphs):
            doc.paragraphs[idx].text = updated_text

        doc.save(output_path)
        logging.info(f"Processed document saved at: '{output_path}'")
        return output_path