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
        model_name="gemini-2.5-pro",
    )

    prompt = f"""
        Analyze the following academic document content using the provided additional context. 
        generate a short text that can be appended to it to enhance 
        its searchability in academic referencing tools such as Google Scholar and PubMed.
        Document Content:
        ---
        {content_sample}
        ---
        Additional Context:
        {additional_context}

        Ensure the output is a text, a sentence.
    """

    try:
        response = await model.generate_content_async(prompt)
        return response.text
            
    except Exception as e:
        logging.error(f"Error calling Gemini API or parsing response: {e}")
        return {}

if __name__ == "__main__":
    async def main():
        """
        Example usage of the get_document_context_with_gemini function.
        """
        sample_content = """
        This document discusses the implications of quantum computing on cryptography, focusing on Shor's algorithm and its potential to break RSA encryption.
        """
        context = "Quantum computing, cryptography, Shor's algorithm, RSA encryption"
        context = await get_document_context_with_gemini(sample_content, context)
        print(context)
    import asyncio
    asyncio.run(main())