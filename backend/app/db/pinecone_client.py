
from pinecone import Pinecone
from app.config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

def query(vector, top_k=5):
    try:
        return index.query(vector=vector, top_k=top_k, include_metadata=True)
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return {"matches": []}

def upsert(vectors):
    try:
        index.upsert(vectors)
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")
        raise
