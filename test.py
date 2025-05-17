import os
import json
from docx import Document
from sqlalchemy.orm import Session
from typing import List, Dict, Optional
from datetime import datetime, date
import logging

# Add subscription plan constants
class SubscriptionPlan:
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"

# Citation limits per subscription plan
CITATION_LIMITS = {
    SubscriptionPlan.FREE: 5,       # Free tier: max 5 citations
    SubscriptionPlan.BASIC: 20,     # Basic tier: max 20 citations
    SubscriptionPlan.PREMIUM: 50,   # Premium tier: max 50 citations
    SubscriptionPlan.ENTERPRISE: -1  # Enterprise: unlimited citations (-1)
}

class InTextCitationProcessor:
    def __init__(self, style="APA", collection_name="general", threshold=0.0, top_k=5, 
                 subscription_plan=SubscriptionPlan.FREE):
        """
        Initialize the citation processor with subscription plan awareness.

        Parameters:
        - style (str): Citation style (APA, MLA, Chicago).
        - collection_name (str): MongoDB collection for vector searches (should be the best-fit category).
        - threshold (float): Minimum similarity threshold for semantic matching.
        - top_k (int): Number of top relevant documents to retrieve.
        - subscription_plan (str): User's subscription plan level.
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
        
        # Store subscription plan and its citation limit
        self.subscription_plan = subscription_plan
        self.citation_limit = CITATION_LIMITS.get(subscription_plan, 5)  # Default to free tier limit
        self.citation_count = 0  # Initialize counter for added citations

        # Load SpaCy model for sentence segmentation
        self.nlp = spacy.load("en_core_web_sm")
        
        logging.info(f"Initialized InTextCitationProcessor with {subscription_plan} plan (limit: {self.citation_limit} citations)")
    
    def get_remaining_citations(self) -> int:
        """
        Get the number of remaining citations available for the current subscription.
        
        Returns:
        - int: Number of citations remaining (-1 for unlimited)
        """
        if self.citation_limit == -1:  # Enterprise/unlimited plan
            return -1
        return max(0, self.citation_limit - self.citation_count)
    
    def can_add_citation(self) -> bool:
        """
        Check if the user can add another citation based on their subscription limit.
        
        Returns:
        - bool: True if the citation can be added, False otherwise
        """
        # If citation_limit is -1, it means unlimited citations
        if self.citation_limit == -1:
            return True
            
        # Otherwise, check if we're under the limit
        return self.citation_count < self.citation_limit
    
    def find_relevant_papers(self, sentence: str, return_all: bool = False):
        """
        Retrieve semantically relevant papers for a sentence using similarity search,
        then filter them by the threshold and respect subscription limits.
        
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

        # If citation limit has been reached, return empty list
        if not self.can_add_citation():
            logging.info(f"Citation limit reached ({self.citation_limit}). Skipping citation for sentence: '{sentence}'")
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

    def process_sentences(self, input_path: str, output_path: str, use_all_citations: bool = False):
        """
        Process each sentence in the document for in-text citations and add references,
        respecting the subscription-based citation limit.

        Parameters:
        - input_path (str): Path to the input document.
        - output_path (str): Path to save the output document.
        - use_all_citations (bool): If True, use all relevant citations; if False, use only the best citation.
        
        Returns:
        - Dict: Processing results including citations added and limit information
        """
        logging.info(f"Starting sentence-level processing for file: '{input_path}'")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        doc = Document(input_path)
        updated_paragraphs = []
        
        # Reset citation counter for this processing run
        self.citation_count = 0
        citations_added = 0
        citations_skipped_due_to_limit = 0

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
                    # Check if we can add more citations according to subscription limit
                    if not self.can_add_citation():
                        logging.info(f"Citation limit reached ({self.citation_limit}). "
                                    f"Skipping citation for sentence: '{sentence_text}'")
                        processed_sentences.append(sentence_text)
                        citations_skipped_due_to_limit += 1
                        continue
                    
                    # Use the return_all parameter to get all relevant papers or just the best one
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
                        
                        # Increment citation counter
                        self.citation_count += 1
                        citations_added += 1

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
        
        # Prepare result information
        result = {
            "file_path": output_path,
            "citations_added": citations_added,
            "citations_limit": self.citation_limit,
            "citations_remaining": self.get_remaining_citations(),
            "citations_skipped_due_to_limit": citations_skipped_due_to_limit,
            "subscription_plan": self.subscription_plan,
            "limit_reached": not self.can_add_citation()
        }
        
        logging.info(f"Processed document saved at: '{output_path}'")
        logging.info(f"Citation statistics: {json.dumps(result, indent=2)}")
        
        return result

    def prepare_citations_for_review(self, input_path: str) -> Dict[str, Any]:
        """
        Prepare in-text citations for frontend review with unique identifiers,
        respecting subscription limits.

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
            
            # Reset citation counter for this analysis run
            self.citation_count = 0
            
            # Prepare citation review data
            citation_review_data = {
                "document_id": str(uuid.uuid4()),
                "total_citations": 0,
                "citations": [],
                "subscription_info": {
                    "plan": self.subscription_plan,
                    "citation_limit": self.citation_limit,
                    "citations_found": 0,
                    "citations_included": 0,
                    "limit_reached": False
                },
                "diagnostics": {
                    "processed_paragraphs": 0,
                    "processed_sentences": 0,
                    "skipped_paragraphs": [],
                    "empty_sentences": [],
                    "skipped_due_to_limit": 0
                }
            }

            # Track current page number
            current_page = 1
            total_citations_found = 0
            
            for para_idx, para in enumerate(doc.paragraphs, start=1):
                paragraph_text = para.text.strip()

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
                        # Find relevant papers without applying subscription limit yet
                        # (so we can count total available citations)
                        relevant_papers = self.mongo_manager.semantic_search(
                            collection_name=self.collection_name,
                            query_text=sentence_text,
                            top_k=self.top_k
                        )
                        
                        # Filter by threshold
                        filtered_papers = [doc for doc in relevant_papers 
                                          if doc.metadata.get("score", 0.0) >= self.threshold]
                        
                        # Count total available citations before limiting
                        total_citations_found += len(filtered_papers)
                        
                        # Now apply subscription limit
                        if not self.can_add_citation():
                            citation_review_data["diagnostics"]["skipped_due_to_limit"] += len(filtered_papers)
                            logging.info(f"Citation limit reached. Skipping {len(filtered_papers)} potential citations.")
                            continue
                            
                        # Only include citations up to the limit
                        remaining = self.get_remaining_citations()
                        if remaining != -1 and len(filtered_papers) > remaining:
                            # Take only as many as we can still include
                            filtered_papers = filtered_papers[:remaining]
                            logging.info(f"Limited to {remaining} citations due to subscription plan.")

                        # Log semantic search results
                        logging.debug(f"Using {len(filtered_papers)} citations for sentence")

                        if not filtered_papers:
                            logging.debug(f"No relevant papers found for sentence: '{sentence_text}'")
                            continue

                        # Prepare citations for each relevant paper
                        for paper_doc in filtered_papers:
                            # Skip if we've reached the citation limit
                            if not self.can_add_citation():
                                citation_review_data["subscription_info"]["limit_reached"] = True
                                break
                                
                            metadata = paper_doc.metadata
                            title = metadata.get("title")
                            
                            if not title:
                                logging.error("Missing 'title' in paper metadata. Skipping this paper.")
                                continue

                            # Fetch additional metadata
                            db_metadata = self.fetch_metadata_from_db(title)
                            authors = db_metadata.get("authors", ["Unknown"])
                            year = db_metadata.get("published_date", "n.d.")
 
                            # Prepare citation details with page number
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
                                "page_number": f"{current_page}({sent_idx})" ,
                                "metadata": {
                                    "paragraph_index": para_idx,
                                    "sentence_index": sent_idx,
                                }
                            }

                            citation_review_data["citations"].append(citation_entry)
                            citation_review_data["total_citations"] += 1
                            self.citation_count += 1

                    except Exception as e:
                        logging.error(f"Error processing sentence '{sentence_text}': {e}")

                # Increment page number after each paragraph
                current_page += 1

            # Update subscription info
            citation_review_data["subscription_info"]["citations_found"] = total_citations_found
            citation_review_data["subscription_info"]["citations_included"] = citation_review_data["total_citations"]
            citation_review_data["subscription_info"]["limit_reached"] = not self.can_add_citation()
            
            # Log final diagnostic information
            logging.info(f"Citation processing completed. Total citations: {citation_review_data['total_citations']}")
            logging.info(f"Total available citations: {total_citations_found}, included: {citation_review_data['total_citations']}")
            logging.info(f"Subscription limit reached: {citation_review_data['subscription_info']['limit_reached']}")

            return citation_review_data

        except Exception as e:
            logging.error(f"Error processing document: {e}")
            raise