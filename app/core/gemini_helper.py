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


async def get_document_context_with_gemini(content: str, additional_context: str) -> str:
    """
    Uses the Gemini API to analyze document content and extract a keyword string for search enhancement.

    Args:
        content: The text content of the document.
        additional_context: User-provided context.

    Returns:
        A string of keywords to be appended to a search query.
    """
    content_sample = content[:4000] if len(content) > 4000 else content

    # Set up the model
    generation_config = {
        "temperature": 0.1,
        "top_p": 0.95,
        "top_k": 0,
        "max_output_tokens": 100,
    }
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
    )

    prompt = f"""
        Analyze the following academic document content and the additional context. 
        Generate a concise set of 5-7 keywords that best represent the document's research context, category, and field of study.
        This keyword set will be used to improve searchability in academic search engines.
        
        Document Content:
        ---
        {content_sample}
        ---
        Additional Context:
        {additional_context}

        Return only the keywords separated by spaces. For example: "quantum computing cryptography Shor's algorithm RSA encryption cybersecurity"
    """

    try:
        response = await model.generate_content_async(prompt)
        return response.text.strip()
            
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return ""

if __name__ == "__main__":
    async def main():
        """
        Example usage of the get_document_context_with_gemini function.
        """
        sample_content = """
        This document discusses the implications of quantum computing on cryptography, focusing on Shor's algorithm and its potential to break RSA encryption.
        """
        context = "Quantum computing, cryptography, Shor's algorithm, RSA encryption"
        keywords = await get_document_context_with_gemini(sample_content, context)
        print(f"Generated keywords: {keywords}")
    import asyncio
    asyncio.run(main())