
from pinecone import Pinecone
from app.config import PINECONE_API_KEY, PINECONE_INDEX

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)

def query(vector, top_k=5, filter=None):
    try:
        return index.query(vector=vector, top_k=top_k, include_metadata=True, filter=filter)
    except Exception as e:
        print(f"Error querying Pinecone: {e}")
        return {"matches": []}

def upsert(vectors):
    try:
        response = index.upsert(vectors)
        return response.upserted_count if hasattr(response, "upserted_count") else len(vectors)
    except Exception as e:
        print(f"Error upserting to Pinecone: {e}")
        raise

def clear_index():
    """Delete ALL vectors from the index."""
    try:
        index.delete(delete_all=True)
        return True
    except Exception as e:
        print(f"Error clearing index: {e}")
        raise

def delete_by_source(source):
    """Delete all vectors belonging to a specific source document (requires Pinecone paid plan)."""
    try:
        index.delete(filter={"source": {"$eq": source}})
        return True
    except Exception as e:
        print(f"Error deleting vectors for source '{source}': {e}")
        raise

def get_index_stats():
    """Return index stats including total vector count."""
    try:
        return index.describe_index_stats()
    except Exception as e:
        print(f"Error fetching index stats: {e}")
        return None
