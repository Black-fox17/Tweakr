import google.generativeai as genai
import json
import logging
from decouple import config
from typing import List, Dict, Any
from pydantic import BaseModel

# Configure API
try:
    # NOTE: Remember to set your GOOGLE_GEMINI_KEY in your environment or a .env file
    genai.configure(api_key=config("GOOGLE_GEMINI_KEY"))
except (KeyError, AttributeError):
    logging.error("GOOGLE_GEMINI_KEY environment variable not set.")
    pass


# Corrected Schemas: Removed 'propertyOrdering'
DOCUMENT_CONTEXT_SCHEMA = {
    "type": "object",
    "properties": {
        "research_context": {"type": "string"},
        "document_category": {"type": "string"},
        "field_keywords": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["research_context", "document_category", "field_keywords"],
}

CITATION_SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "sentences_to_cite": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["sentences_to_cite"],
}


async def enrich_sentence_with_gemini(sentence: str, domain: str) -> str:
    """Enrich a sentence for academic search optimization."""
    if not sentence.strip():
        return ""

    # Using a newer model version can sometimes provide better results
    model = genai.GenerativeModel(model_name="gemini-2.5-pro")
    
    prompt = f"""
    You are an assistant that reformulates short sentences so they are suitable
    for academic and research searches (e.g., Google Scholar, Semantic Scholar, PubMed).  

    Task:
    - Take the given sentence and enrich it with additional context, making it precise and scholarly.  
    - Ensure the sentence is explicitly aligned with the given domain or field: "{domain}".  
    - The enriched version should be clear, formal, and optimized for retrieving research papers in that field.  

    Sentence: {sentence}

    Return only the enriched sentence.
    """

    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return ""


async def get_document_context_with_gemini(content: str, additional_context: str) -> Dict[str, Any]:
    """
    Uses Gemini API to analyze document content and extract context with structured output.

    Args:
        content: The text content of the document.
        additional_context: Additional context for analysis.

    Returns:
        A dictionary containing 'research_context', 'document_category', and 'field_keywords'.
    """
    content_sample = content[:4000] if len(content) > 4000 else content

    model = genai.GenerativeModel(model_name="gemini-2.5-pro")

    prompt = f"""
    Analyze the following academic document content with the provided additional context.
    
    Document Content:
    ---
    {content_sample}
    ---
    Additional Context:
    {additional_context}

    Provide:
    1. research_context: A concise, one-sentence summary of the core research topic or argument.
    2. document_category: The most specific academic field or sub-field it belongs to (e.g., "computational_linguistics", "particle_physics", "macroeconomics"). Use a single, snake_cased string.
    3. field_keywords: A list of 5-7 essential keywords or technical terms from the document.

    Base your analysis solely on the provided content and additional context.
    """

    try:
        response = await model.generate_content_async(
            prompt,
            generation_config={
                "response_mime_type": "application/json",
                "response_schema": DOCUMENT_CONTEXT_SCHEMA,
            }
        )
        
        result = json.loads(response.text)
        
        if all(k in result for k in ['research_context', 'document_category', 'field_keywords']):
            return result
        else:
            logging.warning("Gemini response was missing required keys.")
            return {}
        
    except json.JSONDecodeError as e:
        logging.error(f"Error parsing JSON response: {e}")
        return {}
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return {}


async def select_sentences_for_citation_with_gemini(sentences: List[str]) -> List[str]:
    """
    Uses Gemini API to select sentences that require academic citations.

    Args:
        sentences: A list of sentence strings.

    Returns:
        A list of sentences selected for citation.
    """
    if not sentences:
        return []

    model = genai.GenerativeModel(model_name="gemini-2.5-pro")
    
    def create_chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    sentence_chunks = list(create_chunks(sentences, 50))
    selected_sentences = []

    for chunk in sentence_chunks:
        prompt = f"""
        You are a meticulous research assistant. Your task is to analyze a list of sentences
        and identify which ones require an academic citation choose as many as possible fit based on the length of
        the whole sentences, the length is {len(sentences)}.

        Instructions:
        1. Review the following list of sentences.
        2. Identify every sentence that should be supported by a reference in an academic paper.

        Sentences to Analyze:
        {chunk}
        """

        try:
            response = await model.generate_content_async(
                prompt,
                generation_config={
                    "response_mime_type": "application/json",
                    "response_schema": CITATION_SELECTION_SCHEMA,
                }
            )
            
            result = json.loads(response.text)
            
            if "sentences_to_cite" in result and isinstance(result["sentences_to_cite"], list):
                selected_sentences.extend(result["sentences_to_cite"])
            
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing JSON response: {e}")
            continue
        except Exception as e:
            logging.error(f"Error calling Gemini API: {e}")
            continue

    return selected_sentences


# Example usage
if __name__ == "__main__":
    import asyncio

    async def main():
        """Example usage of the functions."""
        # Test sentence enrichment
        sentence = "Quantum entanglement is a fundamental phenomenon in quantum mechanics."
        enriched = await enrich_sentence_with_gemini(sentence, "quantum computing")
        print(f"Enriched: {enriched}\n")
        
        # Test document context
        content = "This paper examines machine learning algorithms for natural language processing, focusing on transformer architectures. We introduce a novel attention mechanism that improves performance on summarization tasks. Our model, evaluated on the CNN/Daily Mail dataset, achieves state-of-the-art results."
        context = await get_document_context_with_gemini(content, "AI research paper")
        print(f"Context: {json.dumps(context, indent=2)}\n")
        
        # Test citation selection
        test_sentences = [
            "Machine learning has revolutionized many fields.",
            "According to Smith et al. (2023), accuracy improved by 15%.",
            "This is an interesting finding.",
            "The dataset contained 10,000 samples.",
            "Our proposed method outperforms the baseline."
        ]
        citations = await select_sentences_for_citation_with_gemini(test_sentences)
        print(f"Citations needed: {citations}")

    asyncio.run(main())