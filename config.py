import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

api_key = os.getenv("OPENAI_API_KEY", "mock-key")
client = OpenAI(api_key=api_key)
EMBEDDING_MODEL = "text-embedding-3-small"

CHROMA_PATH = "src/data/chromadb"
COLLECTION_NAME = "technical"

# saves data on disk under data/chromdb and not in memory
chroma_client = chromadb.PersistentClient(path = CHROMA_PATH)
# Chroma defaults to l2 but open ai requires cosine
collection = chroma_client.get_or_create_collection(
    name = COLLECTION_NAME,
    metadata = {"hnsw:space":"cosine"}
    )
