import os
import google.generativeai as genai
import json
import logging
from decouple import config

try:
    genai.configure(api_key=config("GOOGLE_GEMINI_KEY"))
except KeyError:
    logging.error("GEMINI_API_KEY environment variable not set.")
    pass

async def enrich_sentence_with_gemini(sentence: str, domain: str) -> str:
    if not sentence.strip():
        return ""

    # Set up the model
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

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
        logging.error(f"Error calling Gemini API or parsing response: {e}")
        return ""

async def get_document_context_with_gemini(content: str, additional_context: str) -> dict:
    """
    Uses the Gemini API to analyze document content and extract context.

    Args:
        content: The text content of the document.

    Returns:
        A dictionary containing 'research_context', 'document_category', and 'field_keywords'.
    """
    content_sample = content[:4000] if len(content) > 4000 else content

    # Set up the model
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    prompt = f"""
        Analyze the following academic document content with the provided additional context.
        and provide a structured JSON output with three keys:
        1. "research_context": A concise, one-sentence summary of the core research topic or argument.
        2. "document_category": The most specific academic field or sub-field it belongs to (e.g., "computational_linguistics", "particle_physics", "macroeconomics"). Use a single, snake_cased string.
        3. "field_keywords": A list of 5-7 essential keywords or technical terms from the document.

        Document Content:
        ---
        {content_sample}
        ---
        Additional Context:
        {additional_context}

        Ensure the output is based solely on the content provided and the additional context TAKE NOTE OF THE ADDITIONAL CONTEXT and make sure to return a structured json response based on the provided keys.
    """

    try:
        response = await model.generate_content_async(prompt)
        result = json.loads(response.text)
        
        # Basic validation
        if all(k in result for k in ['research_context', 'document_category', 'field_keywords']):
            return result
        else:
            logging.warning("Gemini response was missing required keys.")
            return {}
            
    except Exception as e:
        logging.error(f"Error calling Gemini API or parsing response: {e}")
        return {}

# if __name__ == "__main__":
#     async def main():
#         """
#         Example usage of the get_document_context_with_gemini function.
#         """
#         sentence = "Quantum entanglement is a fundamental phenomenon in quantum mechanics."
#         context = await enrich_sentence_with_gemini(sentence, domain="quantum computing")
#         print(context)
#     import asyncio
#     asyncio.run(main())

async def select_sentences_for_citation_with_gemini(sentences: list) -> list:
    """
    Uses the Gemini API to select sentences that require academic citations.

    Args:
        sentences: A list of sentence strings.

    Returns:
        A list of sentences selected for citation.
    """
    if not sentences:
        return []

    # Set up the model
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 8192,
        "response_mime_type": "application/json",
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # Chunk sentences to avoid hitting prompt limits
    def create_chunks(lst, n):
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    sentence_chunks = list(create_chunks(sentences, 50)) # Process 50 sentences at a time
    selected_sentences = []

    for chunk in sentence_chunks:
        prompt = f"""
            You are a meticulous research assistant. Your task is to analyze a list of sentences
            and identify which ones make specific claims, present data, or state facts that
            require an academic citation.

            Instructions:0
            1.  Review the following list of sentences.
            2.  Identify every sentence that should be supported by a reference in an academic paper.
            3.  Return a JSON object with a single key "sentences_to_cite" which contains a list of the exact, unmodified sentences you have selected.

            Example:
            Input sentences: ["The sky is blue.", "This study found a significant correlation.", "I think this is interesting."]
            Output:
            {{
                "sentences_to_cite": ["This study found a significant correlation."]
            }}

            Sentences to Analyze:
            ---
            {json.dumps(chunk)}
            ---

            Return only the JSON object.
        """
        try:
            response = await model.generate_content_async(prompt)
            result = json.loads(response.text)
            if "sentences_to_cite" in result and isinstance(result["sentences_to_cite"], list):
                selected_sentences.extend(result["sentences_to_cite"])
        except Exception as e:
            logging.error(f"Error calling Gemini API or parsing sentence selection response: {e}")
            continue # Continue to the next chunk

    return selected_sentences