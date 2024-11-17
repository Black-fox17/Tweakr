import os
import pinecone

pinecone.init(api_key=os.getenv("PINECONE_API_KEY"), environment="us-west1-gcp")
pinecone_index = pinecone.Index("document-index")
