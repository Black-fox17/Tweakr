from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings
import logging
import os

# Check if the API key is set
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    logging.warning("GOOGLE_API_KEY environment variable is not set. Embeddings will fail.")

# Swapped the embedding for google's embeddings
# embeddings = OpenAIEmbeddings()
try:
    logging.info("Initializing Google Generative AI Embeddings model...")
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    logging.info("Google Generative AI Embeddings model initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Google Generative AI Embeddings model: {e}")
    raise

def embeddings(query):
    try:
        logging.info(f"Generating embeddings for query: {query[:50]}... (truncated)")
        embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        result = embedding_model.embed_query(query)
        logging.info(f"Successfully generated embeddings of length: {len(result)}")
        return result
    except Exception as e:
        logging.error(f"Error generating embeddings: {e}")
        raise