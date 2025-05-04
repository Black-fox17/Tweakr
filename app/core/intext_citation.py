import os
import json
from docx import Document
from sqlalchemy.orm import Session
from typing import List, Dict
from datetime import datetime, date
from datapipeline.core.database import get_session_with_ctx_manager
from datapipeline.models.papers import Papers
from app.core.references_generator import ReferenceGenerator
from datapipeline.core.mongo_client import MongoDBVectorStoreManager
from datapipeline.core.utils import embeddings 
from datapipeline.core.constants import MONGODB_ATLAS_CLUSTER_URI, MONGO_DB_NAME
from app.core.hyperlink_helper import add_hyperlink
from app.core.headings import headers  # Import the headings
import spacy
import logging
import uuid
import json
from typing import List, Dict, Any

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
        self.headers = headers  # Predefined headings (if any)
        self.matched_paper_titles = []  # Store matched paper titles

        # Load SpaCy model for sentence segmentation
        self.nlp = spacy.load("en_core_web_sm")

    def is_dynamic_heading(self, para) -> bool:
        """
        Dynamically detects if a paragraph is a heading or subheading using multiple heuristics.

        Parameters:
        - para: A docx paragraph object.

        Returns:
        - True if the paragraph is likely a heading/subheading; otherwise, False.
        """
        text = para.text.strip()
        if not text:
            return False

        # 1. Check the paragraph style (if available)
        try:
            style_name = para.style.name.lower()
            if "heading" in style_name or "title" in style_name:
                logging.info(f"Detected heading based on style: '{text}'")
                return True
        except Exception as e:
            logging.warning("Could not determine paragraph style.")

        # 2. Check against predefined headers
        if text in self.headers:
            logging.info(f"Detected heading based on predefined headers: '{text}'")
            return True

        # 3. Heuristic: if the text is short (fewer than 8 words) and lacks punctuation,
        # it may be a heading.
        words = text.split()
        if len(words) < 8 and not any(punct in text for punct in [".", "?", "!", ";", ":"]):
            logging.info(f"Detected potential heading based on text heuristic: '{text}'")
            return True

        return False

    def add_references_section(self, doc: Document, category: str):
        """
        Generate and append a references section to the document.
        """
        if not self.matched_paper_titles:
            logging.info("No matched papers to add to the references section.")
            return

        # references is now a list of tuples: (reference_text, url)
        references = self.reference_generator.generate_references(self.matched_paper_titles, category)
        if references:
            # Add a heading for the references section.
            doc.add_paragraph("References")
            for ref_text, ref_url in references:
                para = doc.add_paragraph()
                # Add the main reference text.
                para.add_run(ref_text)
                # If there is a URL, append a label and add the hyperlink.
                if ref_url:
                    # Choose the label based on style.
                    if self.reference_generator.style == "APA":
                        label = " Retrieved from "
                    elif self.reference_generator.style == "MLA":
                        label = " Available at "
                    else:  # Chicago or other
                        label = " "
                    para.add_run(label)
                    add_hyperlink(para, ref_url, ref_url)

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
                # Use the ReferenceGenerator's parse_authors method for consistency
                authors = []
                if getattr(paper, "authors", None):
                    authors = self.reference_generator.parse_authors(paper.authors)
                if not authors:
                    authors = ["Unknown"]

                # Parse publication year
                published_date = "n.d."
                if getattr(paper, "pub_date", None):
                    if isinstance(paper.pub_date, (date, datetime)):
                        published_date = str(paper.pub_date.year)

                metadata = {
                    "authors": authors,
                    "published_date": published_date or "n.d."
                }
                logging.debug(f"Fetched metadata from DB: {metadata}")
                return metadata

            except Exception as e:
                logging.error(f"Error fetching metadata for title '{title}': {e}")
                return {"authors": ["Unknown"], "published_date": "n.d."}

    def format_citation(self, authors: List[str], year: str) -> str:
        """
        Format in-text citation based on the specified style.
        For all styles, uses only first name for single authors and first name + et al. for multiple authors.
        Each citation style's specific formatting conventions are maintained.
        """
        if not authors:
            authors = ["Unknown"]
        if not year or not isinstance(year, str):
            year = "n.d."
        
        # Extract first name from the first author
        first_author = authors[0]
        if " " in first_author:
            first_name = first_author.split(" ")[0]
        else:
            first_name = first_author

        if self.style == "APA":
            # APA: parenthetical citation with comma between author and year
            if len(authors) == 1:
                return f"({first_name}, {year})"
            else:
                return f"({first_name} et al., {year})"
        
        elif self.style == "MLA":
            # MLA: typically includes page numbers but we'll omit them here
            # No comma between author and year in MLA
            if len(authors) == 1:
                return f"({first_name} {year})"
            else:
                return f"({first_name} et al. {year})"
        
        elif self.style == "Chicago":
            # Chicago: parenthetical citations
            # No comma between author and year in Chicago author-date system
            if len(authors) == 1:
                return f"({first_name} {year})"
            else:
                return f"({first_name} et al. {year})"
        
        else:
            raise ValueError(f"Unsupported citation style: {self.style}")
    def find_relevant_papers(self, sentence: str, return_all: bool = False):
        """
        Retrieve semantically relevant papers for a sentence using similarity search,
        then filter them by the threshold.
        
        Parameters:
        - sentence (str): The sentence to find relevant papers for
        - return_all (bool): If True, returns all papers above threshold; 
                            If False, returns only the best matching paper
        
        Returns:
        - List of document objects representing relevant papers
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
            
            # Return all filtered results or just the best one
            return filtered_results if return_all else best_document

        except Exception as e:
            logging.error(f"Error during similarity search for sentence '{sentence}': {e}")
            return []

    def process_sentences(self, input_path: str, output_path: str, use_all_citations: bool = True):
        """
        Process each sentence in the document for in-text citations and add references.

        Parameters:
        - input_path (str): Path to the input document.
        - output_path (str): Path to save the output document.
        - use_all_citations (bool): If True, use all relevant citations; if False, use only the best citation.
        
        Returns:
        - Path to the updated document.
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

            # Use dynamic heading detection to skip headings and subheadings
            if self.is_dynamic_heading(para):
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
                    # Use the return_all parameter to get all relevant papers or just the best one
                    relevant_papers = self.find_relevant_papers(sentence_text, return_all=use_all_citations)
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

                    # Modify the sentence to insert citations before the full stop
                    if citation_texts:
                        # Remove the full stop
                        base_sentence = sentence_text.rstrip('.')
                        # Insert citations before the full stop
                        sentence_text = f"{base_sentence} {' '.join(citation_texts)}."

                except Exception as e:
                    logging.error(f"Error processing sentence '{sentence_text}' in paragraph {para_idx}: {e}")
                    processed_sentences.append(sentence_text)
                    continue

                processed_sentences.append(sentence_text)

            # Reconstruct the paragraph
            final_paragraph_text = " ".join(processed_sentences)
            updated_paragraphs.append(final_paragraph_text)

        # Save updated content back to the document
        for idx, updated_text in enumerate(updated_paragraphs):
            if idx < len(doc.paragraphs):  # Ensure we don't go out of bounds
                doc.paragraphs[idx].text = updated_text

        # Add the references section
        self.add_references_section(doc, self.collection_name)

        doc.save(output_path)
        logging.info(f"Processed document saved at: '{output_path}'")
        return output_path
    
    def prepare_citations_for_review(self, input_path: str) -> Dict[str, Any]:
        """
        Prepare in-text citations for frontend review with unique identifiers.

        Parameters:
        - input_path (str): Path to the input document.

        Returns:
        - Dict containing document-level and citation-level information for review.
        """
        logging.info(f"Preparing citations for review from file: '{input_path}'")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        try:
            # Open the document from the temporary file path
            doc = Document(input_path)
            
            # Diagnostic logging for document structure
            logging.info(f"Document paragraphs count: {len(doc.paragraphs)}")
            
            # Prepare citation review data
            citation_review_data = {
                "document_id": str(uuid.uuid4()),
                "total_citations": 0,
                "citations": [],
                "diagnostics": {
                    "processed_paragraphs": 0,
                    "processed_sentences": 0,
                    "skipped_paragraphs": [],
                    "empty_sentences": []
                }
            }

            for para_idx, para in enumerate(doc.paragraphs, start=1):
                paragraph_text = para.text.strip()

                # Diagnostic logging for paragraph content
                logging.debug(f"Paragraph {para_idx} text: '{paragraph_text}'")

                if not paragraph_text:
                    citation_review_data["diagnostics"]["skipped_paragraphs"].append(para_idx)
                    continue

                if self.is_dynamic_heading(para):
                    logging.info(f"Skipping heading paragraph: '{paragraph_text}'")
                    citation_review_data["diagnostics"]["skipped_paragraphs"].append(para_idx)
                    continue

                # Increment processed paragraphs
                citation_review_data["diagnostics"]["processed_paragraphs"] += 1

                # Tokenize paragraph into sentences
                try:
                    sentences = list(self.nlp(paragraph_text).sents)
                except Exception as tokenize_error:
                    logging.error(f"Error tokenizing paragraph {para_idx}: {tokenize_error}")
                    continue

                for sent_idx, sent in enumerate(sentences, start=1):
                    sentence_text = sent.text.strip()

                    # Track processed sentences
                    citation_review_data["diagnostics"]["processed_sentences"] += 1

                    if not sentence_text:
                        citation_review_data["diagnostics"]["empty_sentences"].append({
                            "paragraph": para_idx,
                            "sentence_index": sent_idx
                        })
                        continue

                    try:
                        # Diagnostic logging for semantic search
                        logging.debug(f"Performing semantic search for sentence: '{sentence_text}'")
                        
                        relevant_papers = self.find_relevant_papers(sentence_text)
                        
                        # Log semantic search results
                        logging.debug(f"Semantic search for sentence returned {len(relevant_papers)} papers")

                        if not relevant_papers:
                            logging.debug(f"No relevant papers found for sentence: '{sentence_text}'")
                            continue

                        # Prepare citations for each relevant paper
                        for paper_doc in relevant_papers:
                            metadata = paper_doc.metadata
                            title = metadata.get("title")
                            
                            if not title:
                                logging.error("Missing 'title' in paper metadata. Skipping this paper.")
                                continue

                            # Fetch additional metadata
                            db_metadata = self.fetch_metadata_from_db(title)
                            authors = db_metadata.get("authors", ["Unknown"])
                            year = db_metadata.get("published_date", "n.d.")

                            # Prepare citation details
                            citation_id = str(uuid.uuid4())
                            citation_entry = {
                                "id": citation_id,
                                "original_sentence": sentence_text,
                                "paper_details": {
                                    "title": title,
                                    "authors": authors,
                                    "year": year,
                                    "url": metadata.get("url", ""),
                                    "doi": metadata.get("doi", "")
                                },
                                "status": "pending_review",
                                "metadata": {
                                    "paragraph_index": para_idx,
                                    "sentence_index": sent_idx
                                }
                            }

                            citation_review_data["citations"].append(citation_entry)
                            citation_review_data["total_citations"] += 1

                    except Exception as e:
                        logging.error(f"Error processing sentence '{sentence_text}': {e}")

            # Log final diagnostic information
            logging.info(f"Citation processing completed. Total citations: {citation_review_data['total_citations']}")
            logging.info(f"Diagnostics: {json.dumps(citation_review_data['diagnostics'], indent=2)}")

            return citation_review_data

        except Exception as e:
            logging.error(f"Error processing document: {e}")
            raise

    def update_document_with_reviewed_citations(self, reviewed_citations: List[Dict[str, Any]]) -> List[str]:
        """
        Process reviewed citations and return formatted references.

        Parameters:
        - reviewed_citations (List[Dict]): List of citations with their review status.

        Returns:
        - List[str]: List of formatted references.
        """
        logging.info("Processing reviewed citations for formatted references")

        formatted_references = []
        processed_titles = set()  # To avoid duplicate references

        for citation in reviewed_citations:
            if citation.get('status') != 'accepted':
                continue

            paper_details = citation.get('paper_details', {})
            title = paper_details.get('title')
            
            # Skip if we've already processed this title
            if title in processed_titles:
                continue
            
            processed_titles.add(title)
            
            # Get authors, year, and page number
            authors = paper_details.get('authors', ["Unknown"])
            year = paper_details.get('year', "n.d.")
            url = paper_details.get('url', "")
            page_number = paper_details.get('page_number', "")
            
            # Format the reference
            if self.style == "APA":
                # Format authors with full names
                if len(authors) == 1:
                    author_str = f"{authors[0]}"
                else:
                    author_str = f"{authors[0]} et al."
                
                # Format the reference with page number
                reference = f'{author_str} ({year}). "{title}"'
                if page_number:
                    reference += f' {page_number}'
                if url:
                    reference += f'. Retrieved from {url}'
                
                formatted_references.append(reference)
            
            elif self.style == "MLA":
                # Format authors with full names
                if len(authors) == 1:
                    author_str = f"{authors[0]}"
                else:
                    author_str = f"{authors[0]}, et al."
                
                # Format the reference with page number
                reference = f'{author_str} "{title}"'
                if page_number:
                    reference += f' {page_number}'
                if url:
                    reference += f'. Available at {url}'
                
                formatted_references.append(reference)
            
            elif self.style == "Chicago":
                # Format authors with full names
                if len(authors) == 1:
                    author_str = f"{authors[0]}"
                else:
                    author_str = f"{authors[0]}, et al."
                
                # Format the reference with page number
                reference = f'{author_str} "{title}"'
                if page_number:
                    reference += f' {page_number}'
                if url:
                    reference += f'. {url}'
                
                formatted_references.append(reference)

        return formatted_references
