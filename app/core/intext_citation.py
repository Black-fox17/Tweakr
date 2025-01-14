import os
import json
from docx import Document
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, date
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from core.references_generator import ReferenceGenerator
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from datapipeline.core.utils import embeddings 
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from core.headings import headers  # Import the headings
import spacy
import logging

# Load SpaCy model for sentence segmentation
nlp = spacy.load("en_core_web_sm")

# Setup logging
logging.basicConfig(level=logging.INFO)




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
        self.matched_paper_titles = []  # Store matched paper titles

        # Load SpaCy model for sentence segmentation
        self.nlp = spacy.load("en_core_web_sm")


    def add_references_section(self, doc: Document, category: str):
        """
        Generate and append a references section to the document.

        Parameters:
        - doc (Document): The document to modify.
        - category (str): Category of the papers.
        """
        if not self.matched_paper_titles:
            logging.info("No matched papers to add to the references section.")
            return

        references = self.reference_generator.generate_references(self.matched_paper_titles, category)
        if references:
            # Add a heading for the references section
            doc.add_paragraph("References")

            # Add each reference as a new paragraph
            for ref in references:
                doc.add_paragraph(ref)

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
                    if isinstance(paper.pub_date, (date, datetime)):
                        published_date = str(paper.pub_date.year)

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
                query_text=sentence,
                top_k=self.top_k
            )
            logging.debug(f"Raw similarity search returned {len(results)} documents for sentence: '{sentence}'")

            # Filter by threshold
            filtered_results = []
            best_document = []
            highest_score = float('-inf')

            # for doc in results:
            #     metadata = doc.metadata
            #     score = metadata.get("score", 0.0)
            #     print("SCORE: ", score)
            #     # TODO: store the score of the document and if one is higher than the last stored score store it and replace the last stored score and document for all the retrieved papers.
            #     if score >= self.threshold:
            #         highest_score = score
            #         filtered_results.append(doc)
            #         if score >= highest_score:
            #             highest_score = score
            #             best_document.clear()
            #             best_document.append(doc)

            for doc in results:
                metadata = doc.metadata
                score = metadata.get("score", 0.0)

                if score >= self.threshold:
                    filtered_results.append(doc)

                    if score > highest_score:
                        highest_score = score
                        best_document.clear()  # Ensure only one document is in the list
                        best_document.append(doc)
                else:
                    logging.debug(
                        f"Document '{doc.metadata.get('title', 'Unknown')}' "
                        f"filtered out with score {score:.2f} < threshold {self.threshold:.2f}"
                    )

            if not filtered_results:
                logging.info(
                    f"No documents found above threshold={self.threshold} for sentence: '{sentence}'"
                )
            
            return best_document

        except Exception as e:
            logging.error(f"Error during similarity search for sentence '{sentence}': {e}")
            return []


    def process_sentences(self, input_path: str, output_path: str):
        """
        Process each sentence in the document for in-text citations and add references.

        Parameters:
        - input_path (str): Path to the input document.
        - output_path (str): Path to save the output document.
        - category (str): Category of the papers for generating references.
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
                        metadata = paper_doc.metadata
                        title = metadata.get("title")
                        if title and title not in self.matched_paper_titles:
                            self.matched_paper_titles.append(title)

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

        # Add the references section
        self.add_references_section(doc, self.collection_name)

        doc.save(output_path)
        logging.info(f"Processed document saved at: '{output_path}'")
        return output_path