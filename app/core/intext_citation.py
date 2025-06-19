import os
import json
import uuid
import random
import logging
import spacy
from docx import Document
from typing import List, Dict, Any
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO)

class AcademicCitationProcessor:
    """
    Enhanced replacement for MongoDB-based citation processor using multiple academic search APIs.
    Provides fallback mechanisms and improved error handling with proper termination controls.
    """
    
    def __init__(self, style="APA", search_providers=None, threshold=0.0, top_k=5, max_api_calls=None):
        self.style = style
        self.search_providers = search_providers or ["semantic_scholar", "crossref", "openalex"]
        self.threshold = threshold
        self.top_k = top_k
        self.max_api_calls = max_api_calls
        self.api_call_count = 0
        self.matched_paper_titles = []
        self._lock = threading.Lock()
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logging.error("SpaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
            raise
        
        self.rate_limits = {
            'semantic_scholar': 0.05,
            'crossref': 0.03,
            'openalex': 0.03
        }
        
        self.last_api_call = {}
        
        self.academic_domains = [
            'healthcare', 'medicine', 'biology', 'computer science', 'machine learning',
            'business', 'management', 'marketing', 'mathematics', 'physics', 
            'neuroscience', 'psychology', 'education', 'engineering', 'nursing',
            'public health', 'clinical', 'research', 'evidence-based', 'systematic'
        ]
        
        self.paper_cache = {}

    def _calculate_api_limits_and_eta(self, total_sentences: int) -> tuple:
        if self.max_api_calls is not None:
            return self.max_api_calls, 0
        
        citation_rate = 1
        avg_providers_per_search = 2
        estimated_citations = int(total_sentences * citation_rate)
        calculated_max_calls = min(estimated_citations * avg_providers_per_search, 150)
        calculated_max_calls = max(calculated_max_calls, 300)
        
        avg_time_per_call = 0.3
        estimated_eta_seconds = calculated_max_calls * avg_time_per_call
        
        self.max_api_calls = int(calculated_max_calls)
        
        return self.max_api_calls, estimated_eta_seconds
    
    def smart_sentence_selection(self, all_sentences: list, max_sentences: int = None) -> list:
        if not all_sentences:
            return []
        
        if max_sentences is None:
            max_sentences = min(len(all_sentences), 200)
        
        if len(all_sentences) <= max_sentences:
            return all_sentences
        
        selected_sentences = []
        
        academic_keywords = set([
            'study', 'research', 'analysis', 'data', 'results', 'findings', 'evidence',
            'method', 'approach', 'theory', 'model', 'framework', 'hypothesis',
            'significant', 'correlation', 'impact', 'effect', 'relationship',
            'according', 'reported', 'demonstrated', 'showed', 'indicated',
            'clinical', 'patient', 'treatment', 'therapy', 'intervention',
            'algorithm', 'system', 'performance', 'evaluation', 'assessment'
        ])
        
        priority_sentences = []
        regular_sentences = []
        
        for sentence in all_sentences:
            sentence_words = set(sentence['text'].lower().split())
            if sentence_words.intersection(academic_keywords):
                priority_sentences.append(sentence)
            else:
                regular_sentences.append(sentence)
        
        stratified_selection = []
        
        paragraphs = defaultdict(list)
        for sentence in all_sentences:
            paragraphs[sentence['actual_para_idx']].append(sentence)
        
        para_keys = list(paragraphs.keys())
        para_count = len(para_keys)
        
        if para_count <= 5:
            sentences_per_para = max_sentences // para_count
            for para_idx in para_keys:
                para_sentences = paragraphs[para_idx]
                if len(para_sentences) <= sentences_per_para:
                    stratified_selection.extend(para_sentences)
                else:
                    priority_in_para = [s for s in para_sentences if s in priority_sentences]
                    regular_in_para = [s for s in para_sentences if s not in priority_sentences]
                    
                    priority_count = min(len(priority_in_para), sentences_per_para // 2)
                    regular_count = sentences_per_para - priority_count
                    
                    selected_priority = random.sample(priority_in_para, priority_count) if priority_in_para else []
                    selected_regular = random.sample(regular_in_para, min(regular_count, len(regular_in_para))) if regular_in_para else []
                    
                    stratified_selection.extend(selected_priority + selected_regular)
        else:
            sections = para_count // 3
            section_size = para_count // sections
            
            for i in range(sections):
                start_idx = i * section_size
                end_idx = start_idx + section_size if i < sections - 1 else para_count
                section_paras = para_keys[start_idx:end_idx]
                
                section_sentences = []
                for para_idx in section_paras:
                    section_sentences.extend(paragraphs[para_idx])
                
                section_quota = max_sentences // sections
                if len(section_sentences) <= section_quota:
                    stratified_selection.extend(section_sentences)
                else:
                    priority_in_section = [s for s in section_sentences if s in priority_sentences]
                    regular_in_section = [s for s in section_sentences if s not in priority_sentences]
                    
                    priority_count = min(len(priority_in_section), section_quota // 2)
                    regular_count = section_quota - priority_count
                    
                    selected_priority = random.sample(priority_in_section, priority_count) if priority_in_section else []
                    selected_regular = random.sample(regular_in_section, min(regular_count, len(regular_in_section))) if regular_in_section else []
                    
                    stratified_selection.extend(selected_priority + selected_regular)
        
        if len(stratified_selection) < max_sentences:
            remaining_sentences = [s for s in all_sentences if s not in stratified_selection]
            additional_needed = max_sentences - len(stratified_selection)
            additional_selected = random.sample(remaining_sentences, min(additional_needed, len(remaining_sentences)))
            stratified_selection.extend(additional_selected)
        elif len(stratified_selection) > max_sentences:
            stratified_selection = random.sample(stratified_selection, max_sentences)
        
        return stratified_selection


    def is_dynamic_heading(self, para) -> bool:
        """
        Dynamically detects if a paragraph is a heading or subheading using multiple heuristics.
        """
        text = para.text.strip()
        if not text:
            return False

        try:
            style_name = para.style.name.lower()
            if "heading" in style_name or "title" in style_name:
                logging.info(f"Detected heading based on style: '{text}'")
                return True
        except Exception:
            pass

        # Heuristic: short text without punctuation or bullet points
        words = text.split()
        if len(words) < 8 and not any(punct in text for punct in [".", "?", "!", ";", ":"]):
            # Skip bullet points and numbered lists
            if not (text.startswith('-') or text.startswith('•') or text[0].isdigit()):
                logging.info(f"Detected potential heading based on text heuristic: '{text}'")
                return True

        return False

    def clean_query(self, query: str) -> str:
        """Clean and optimize search query"""
        if not query or not isinstance(query, str):
            return ""
        
        # Remove bullet points and numbering
        query = query.strip()
        if query.startswith('-') or query.startswith('•'):
            query = query[1:].strip()
        
        # Remove leading numbers
        if query and query[0].isdigit() and '.' in query[:5]:
            query = query.split('.', 1)[1].strip()
        
        # Limit query length
        words = query.split()
        if len(words) > 15:
            query = ' '.join(words[:15])
        
        return query

    async def search_all_providers_async(self, query: str, max_results: int = None) -> List[Dict]:
        if self.api_call_count >= self.max_api_calls:
            return []
        
        query = self.clean_query(query)
        if not query:
            return []
        
        cache_key = f"{query}_{max_results or self.top_k}"
        if cache_key in self.paper_cache:
            return self.paper_cache[cache_key]
        
        max_results = max_results or self.top_k
        
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        timeout = aiohttp.ClientTimeout(total=8, connect=3)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            tasks = []
            
            for provider in self.search_providers:
                if self.api_call_count >= self.max_api_calls:
                    break
                
                with self._lock:
                    if self.api_call_count >= self.max_api_calls:
                        break
                    self.api_call_count += 1
                
                task = self._search_provider_async(session, provider, query, max_results)
                tasks.append(task)
            
            if not tasks:
                return []
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_papers = []
            seen_titles = set()
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                
                for paper in result:
                    title = paper.get('title', '').lower().strip()
                    if title and title not in seen_titles:
                        seen_titles.add(title)
                        all_papers.append(paper)
                        
                        if len(all_papers) >= max_results * 2:
                            break
                
                if len(all_papers) >= max_results * 2:
                    break
        
        self.paper_cache[cache_key] = all_papers
        return all_papers

    async def _search_provider_async(self, session: aiohttp.ClientSession, provider: str, query: str, max_results: int) -> List[Dict]:
        try:
            if provider == 'semantic_scholar':
                return await self._search_semantic_scholar_async(session, query, max_results)
            elif provider == 'crossref':
                return await self._search_crossref_async(session, query, max_results)
            elif provider == 'openalex':
                return await self._search_openalex_async(session, query, max_results)
        except Exception as e:
            logging.error(f"Failed to search {provider}: {e}")
            return []

    async def _search_semantic_scholar_async(self, session: aiohttp.ClientSession, query: str, max_results: int) -> List[Dict]:
        try:
            url = 'https://api.semanticscholar.org/graph/v1/paper/search'
            params = {
                'query': query,
                'limit': min(max_results, 50),
                'fields': 'title,authors,year,venue,citationCount,url,paperId,journal'
            }
            
            async with session.get(url, params=params) as response:
                if response.status == 429:
                    await asyncio.sleep(1)
                    return []
                
                response.raise_for_status()
                data = await response.json()
                
                papers = []
                for paper in data.get('data', []):
                    title = paper.get('title')
                    if not title:
                        continue
                    
                    authors = []
                    for author in paper.get('authors', []):
                        if author and isinstance(author, dict):
                            name = author.get('name')
                            if name:
                                authors.append(name)
                    
                    if not authors:
                        continue
                    
                    journal_info = paper.get('journal', {}) or {}
                    page_info = journal_info.get('pages', '') if isinstance(journal_info, dict) else ''
                    
                    paper_data = {
                        'title': title,
                        'authors': authors,
                        'year': paper.get('year'),
                        'venue': paper.get('venue') or '',
                        'url': paper.get('url') or '',
                        'citations': paper.get('citationCount', 0),
                        'paper_id': paper.get('paperId') or '',
                        'source': 'Semantic Scholar',
                        'page': page_info
                    }
                    papers.append(paper_data)
                
                return papers
        except Exception as e:
            logging.error(f"Error searching Semantic Scholar: {e}")
            return []

    async def _search_crossref_async(self, session: aiohttp.ClientSession, query: str, max_results: int) -> List[Dict]:
        try:
            url = 'https://api.crossref.org/works'
            params = {
                'query': query,
                'rows': min(max_results, 50),
                'sort': 'relevance'
            }
            
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                papers = []
                for item in data.get('message', {}).get('items', []):
                    title_list = item.get('title', [])
                    if not title_list:
                        continue
                    title = ' '.join(title_list) if isinstance(title_list, list) else str(title_list)
                    
                    authors = []
                    for author in item.get('author', []):
                        if author and isinstance(author, dict):
                            if 'given' in author and 'family' in author:
                                authors.append(f"{author['given']} {author['family']}")
                            elif 'family' in author:
                                authors.append(author['family'])
                    
                    if not authors:
                        continue
                    
                    year = None
                    try:
                        if 'published-print' in item:
                            year = item['published-print']['date-parts'][0][0]
                        elif 'published-online' in item:
                            year = item['published-online']['date-parts'][0][0]
                    except (IndexError, KeyError, TypeError):
                        pass
                    
                    venue = ''
                    container_title = item.get('container-title', [])
                    if container_title:
                        venue = container_title[0] if isinstance(container_title, list) else str(container_title)
                    
                    page_info = item.get('page', '')
                    
                    paper_data = {
                        'title': title,
                        'authors': authors,
                        'year': year,
                        'venue': venue,
                        'url': item.get('URL', ''),
                        'citations': item.get('is-referenced-by-count', 0),
                        'doi': item.get('DOI', ''),
                        'source': 'Crossref',
                        'page': page_info
                    }
                    papers.append(paper_data)
                
                return papers
        except Exception as e:
            logging.error(f"Error searching Crossref: {e}")
            return []

    async def _search_openalex_async(self, session: aiohttp.ClientSession, query: str, max_results: int) -> List[Dict]:
        try:
            url = 'https://api.openalex.org/works'
            params = {
                'search': query,
                'per-page': min(max_results, 50),
                'sort': 'relevance_score:desc'
            }
            
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                
                papers = []
                for work in data.get('results', []):
                    title = work.get('title')
                    if not title:
                        continue
                    
                    authors = []
                    for authorship in work.get('authorships', []):
                        if authorship and isinstance(authorship, dict):
                            author = authorship.get('author', {})
                            if author and author.get('display_name'):
                                authors.append(author['display_name'])
                    
                    if not authors:
                        continue
                    
                    venue = ''
                    primary_location = work.get('primary_location', {})
                    if primary_location and isinstance(primary_location, dict):
                        source = primary_location.get('source', {})
                        if source and isinstance(source, dict):
                            venue = source.get('display_name', '')
                    
                    url_val = ''
                    if primary_location and isinstance(primary_location, dict):
                        url_val = primary_location.get('landing_page_url', '')
                    
                    biblio = work.get('biblio', {}) or {}
                    page_info = ''
                    if isinstance(biblio, dict):
                        first_page = biblio.get('first_page', '')
                        last_page = biblio.get('last_page', '')
                        if first_page and last_page:
                            page_info = f"{first_page}-{last_page}"
                        elif first_page:
                            page_info = first_page
                    
                    paper_data = {
                        'title': title,
                        'authors': authors,
                        'year': work.get('publication_year'),
                        'venue': venue,
                        'url': url_val,
                        'citations': work.get('cited_by_count', 0),
                        'doi': work.get('doi', ''),
                        'source': 'OpenAlex',
                        'page': page_info
                    }
                    papers.append(paper_data)
                
                return papers
        except Exception as e:
            logging.error(f"Error searching OpenAlex: {e}")
            return []


    def calculate_relevance_score(self, sentence: str, paper: Dict) -> float:
        """
        Calculate a relevance score between a sentence and a paper.
        Enhanced scoring system with domain relevance and author quality check.
        """
        if not sentence or not isinstance(sentence, str):
            return 0.0
        
        # Check if paper has valid authors - this is a requirement
        authors = paper.get('authors', [])
        if not authors or len(authors) == 0:
            return 0.0
        
        # Check for valid author names
        valid_authors = [author for author in authors if author and str(author).strip()]
        if not valid_authors:
            return 0.0
        
        sentence_lower = sentence.lower()
        title = paper.get('title', '')
        abstract = paper.get('abstract', '')
        
        # Handle None values safely
        if not title:
            title = ''
        if not abstract:
            abstract = ''
        
        title_lower = title.lower()
        abstract_lower = abstract.lower()
        
        # Simple keyword matching score
        sentence_words = set(sentence_lower.split())
        title_words = set(title_lower.split())
        abstract_words = set(abstract_lower.split())
        
        # Remove common stop words for better matching
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        sentence_words = sentence_words - stop_words
        title_words = title_words - stop_words
        abstract_words = abstract_words - stop_words
        
        if not sentence_words:  # If no meaningful words left
            return 0.0
        
        # Calculate overlap scores
        title_overlap = len(sentence_words.intersection(title_words)) / len(sentence_words)
        abstract_overlap = len(sentence_words.intersection(abstract_words)) / len(sentence_words)
        
        # Weight title matches higher than abstract matches
        relevance_score = (title_overlap * 0.8) + (abstract_overlap * 0.2)
        
        # Check for academic domain relevance
        domain_boost = 0
        for domain in self.academic_domains:
            if domain in sentence_lower or domain in title_lower or domain in abstract_lower:
                domain_boost += 0.1
        
        relevance_score += min(domain_boost, 0.2)  # Cap domain boost
        
        # Boost score for recent papers and high citation counts
        year = paper.get('year')
        if year and isinstance(year, (int, str)) and str(year).isdigit():
            year_int = int(year)
            if year_int >= 2020:
                relevance_score *= 1.2
            elif year_int >= 2015:
                relevance_score *= 1.1
            elif year_int >= 2010:
                relevance_score *= 1.05
        
        citations = paper.get('citations', 0)
        if isinstance(citations, (int, str)) and str(citations).isdigit():
            citations_int = int(citations)
            if citations_int > 100:
                relevance_score *= 1.1
            elif citations_int > 50:
                relevance_score *= 1.05
            elif citations_int > 10:
                relevance_score *= 1.02
        
        # Boost papers with multiple authors (indicates collaborative research)
        if len(valid_authors) > 1:
            relevance_score *= 1.05
        
        # Boost papers from reputable venues
        venue = paper.get('venue', '').lower()
        high_impact_keywords = ['journal', 'proceedings', 'conference', 'review', 'nature', 'science', 'ieee', 'acm']
        if any(keyword in venue for keyword in high_impact_keywords):
            relevance_score *= 1.05
        
        return min(relevance_score, 1.0)  # Cap at 1.0

    def batch_process_sentences(self, sentences: list, batch_size: int = 5) -> list:
        all_citations = []
        
        for i in range(0, len(sentences), batch_size):
            if self.api_call_count >= self.max_api_calls:
                break
                
            batch = sentences[i:i + batch_size]
            
            with ThreadPoolExecutor(max_workers=min(3, len(batch))) as executor:
                future_to_sentence = {
                    executor.submit(self.process_single_sentence, sentence): sentence 
                    for sentence in batch
                }
                
                for future in as_completed(future_to_sentence):
                    if self.api_call_count >= self.max_api_calls:
                        break
                        
                    sentence = future_to_sentence[future]
                    try:
                        citation = future.result(timeout=10)
                        if citation:
                            all_citations.append(citation)
                    except Exception as e:
                        logging.error(f"Error processing sentence: {e}")
                        continue
        
        return all_citations

    def process_single_sentence(self, sentence_data: dict) -> dict:
        try:
            sentence_text = sentence_data['text']
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                papers = loop.run_until_complete(self.search_all_providers_async(sentence_text))
            finally:
                loop.close()
            
            if not papers:
                return None
            
            relevant_papers = []
            for paper in papers:
                try:
                    authors = paper.get('authors', [])
                    if not authors:
                        continue
                    
                    valid_authors = [author for author in authors if author and str(author).strip()]
                    if not valid_authors:
                        continue
                    
                    paper['authors'] = valid_authors
                    relevance_score = self.calculate_relevance_score(sentence_text, paper)
                    
                    if relevance_score >= self.threshold:
                        paper['relevance_score'] = relevance_score
                        relevant_papers.append(paper)
                except Exception as e:
                    continue
            
            if not relevant_papers:
                return None
            
            best_paper = max(relevant_papers, key=lambda x: x.get('relevance_score', 0))
            
            year = best_paper.get('year')
            if not year or year == 'None' or (isinstance(year, (int, str)) and str(year).isdigit() and int(year) < 2015):
                return None
            
            page_number = best_paper.get('page', '') or best_paper.get('pages', '') or best_paper.get('page_number', '')
            
            citation_entry = {
                "id": str(uuid.uuid4()),
                "original_sentence": sentence_text,
                "paper_details": {
                    "title": best_paper.get('title'),
                    "authors": best_paper.get('authors', []),
                    "year": str(year) if year != 'None' else "n.d.",
                    "url": best_paper.get('url', ''),
                    "doi": best_paper.get('doi', ''),
                    "venue": best_paper.get('venue', ''),
                    "citations": best_paper.get('citations', 0),
                    "relevance_score": round(best_paper.get('relevance_score', 0), 3),
                    "source": best_paper.get('source', 'Unknown')
                },
                "status": "pending_review",
                "page_number": page_number,
                "search_providers": self.search_providers,
                "metadata": {
                    "paragraph_index": sentence_data['actual_para_idx'],
                    "sentence_index": sentence_data['sent_idx'],
                    "original_document_index": sentence_data['original_doc_idx'],
                    "processing_order": sentence_data.get('processing_order', 0)
                }
            }
            
            return citation_entry
            
        except Exception as e:
            logging.error(f"Error in process_single_sentence: {e}")
            return None

    def prepare_citations_for_review(self, input_path: str, max_paragraphs: int = 100, 
                            random_sample: bool = True) -> Dict[str, Any]:
        logging.info(f"Preparing citations for review using providers {self.search_providers} from file: '{input_path}'")

        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file '{input_path}' does not exist.")

        try:
            doc = Document(input_path)
            total_paragraphs = len(doc.paragraphs)
            logging.info(f"Document paragraphs count: {total_paragraphs}")
            
            paragraphs_to_process = min(total_paragraphs, max_paragraphs)
            logging.info(f"Will process {paragraphs_to_process} out of {total_paragraphs} paragraphs")
            
            if random_sample and total_paragraphs > paragraphs_to_process:
                paragraph_indices = sorted(random.sample(range(total_paragraphs), paragraphs_to_process))
                paragraphs_to_process_list = [doc.paragraphs[i] for i in paragraph_indices]
            else:
                paragraphs_to_process_list = doc.paragraphs[:paragraphs_to_process]
                paragraph_indices = list(range(paragraphs_to_process))
            
            all_sentences = []
            for para_idx, para in enumerate(paragraphs_to_process_list):
                actual_para_idx = paragraph_indices[para_idx] + 1 if random_sample else para_idx + 1
                paragraph_text = para.text.strip()

                if not paragraph_text or self.is_dynamic_heading(para):
                    continue

                try:
                    sentences = list(self.nlp(paragraph_text).sents)
                    for sent_idx, sent in enumerate(sentences, start=1):
                        sentence_text = sent.text.strip()
                        if sentence_text and len(sentence_text) >= 15:
                            all_sentences.append({
                                'text': sentence_text,
                                'para_idx': para_idx,
                                'actual_para_idx': actual_para_idx,
                                'sent_idx': sent_idx,
                                'original_doc_idx': paragraph_indices[para_idx] if random_sample else para_idx
                            })
                except Exception as tokenize_error:
                    logging.error(f"Error tokenizing paragraph {para_idx}: {tokenize_error}")
                    continue

            total_sentences = len(all_sentences)
            logging.info(f"Total sentences found: {total_sentences}")
            
            calculated_max_calls, estimated_eta = self._calculate_api_limits_and_eta(total_sentences)
            logging.info(f"API call limit set to: {calculated_max_calls}")
            
            selected_sentences = self.smart_sentence_selection(all_sentences, min(total_sentences, 150))
            logging.info(f"Selected {len(selected_sentences)} sentences for processing")

            citation_review_data = {
                "document_id": str(uuid.uuid4()),
                "total_citations": 0,
                "citations": [],
                "diagnostics": {
                    "processed_paragraphs": 0,
                    "processed_sentences": 0,
                    "total_sentences_found": total_sentences,
                    "selected_sentences": len(selected_sentences),
                    "skipped_paragraphs": [],
                    "empty_sentences": [],
                    "selected_paragraph_indices": paragraph_indices,
                    "search_providers_used": self.search_providers,
                    "api_calls_made": 0,
                    "max_api_calls": calculated_max_calls,
                    "estimated_eta_seconds": estimated_eta,
                    "errors": [],
                    "terminated_early": False,
                    "termination_reason": None
                }
            }

            for i, sentence in enumerate(selected_sentences):
                sentence['processing_order'] = i + 1

            citations = self.batch_process_sentences(selected_sentences, batch_size=3)
            
            citation_review_data["citations"] = citations
            citation_review_data["total_citations"] = len(citations)
            citation_review_data["diagnostics"]["api_calls_made"] = self.api_call_count
            citation_review_data["diagnostics"]["processed_sentences"] = len(selected_sentences)
            citation_review_data["diagnostics"]["processed_paragraphs"] = len(set(s['para_idx'] for s in selected_sentences))
            
            if self.api_call_count >= self.max_api_calls:
                citation_review_data["diagnostics"]["terminated_early"] = True
                citation_review_data["diagnostics"]["termination_reason"] = "API call limit reached"
            
            logging.info(f"Citation processing completed. Total citations: {citation_review_data['total_citations']}")
            logging.info(f"API calls made: {self.api_call_count}/{self.max_api_calls}")
            
            return citation_review_data

        except Exception as e:
            logging.error(f"Error processing document: {e}")
            raise