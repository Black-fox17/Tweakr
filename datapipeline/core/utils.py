from langchain_google_genai import GoogleGenerativeAIEmbeddings
# from langchain_community.embeddings import OpenAIEmbeddings


# Swapped the embedding for google's embeddings
# embeddings = OpenAIEmbeddings()
embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")