from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings


# Swapped the embedding for google's embeddings
# embeddings = OpenAIEmbeddings()
embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

def embeddings(query):
    embedding_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    return embedding_model.embed_query(query)