
import os
from dotenv import load_dotenv

load_dotenv()


MONGO_DB_NAME = "tweakr_papers_store"
ATLAS_VECTOR_SEARCH_INDEX_NAME = "tweakr-papers-index-vectorstores"
SQLALCHEMY_DATABASE_URL = os.getenv("POSTGRES_DATABASE_URL")
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGO_DATABASE_URL")
ELSEVIER_API_KEY = os.getenv("ELSEVIER_API_KEY")
IEEE_API_KEY = os.getenv("IEEE_API_KEY")
SPRINGER_API_KEY = os.getenv("SPRINGER_API_KEY")
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_GEMINI_KEY")