
import json
import logging
import os
from langchain_openai import OpenAIEmbeddings
from app.db.pinecone_client import query

logger = logging.getLogger(__name__)
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), "../db/feedback.json")

def retrieve(query_text, department=None):
    try:
        emb = embedder.embed_query(query_text)
        filter_dict = {"department": {"$eq": department}} if department else None
        results = query(emb, filter=filter_dict)
        return [{"text": m["metadata"]["text"], "images": m["metadata"].get("images", [])}
                for m in results.get("matches", [])]
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        return []

def store_feedback(unmatched_query):
    try:
        os.makedirs(os.path.dirname(_FEEDBACK_FILE), exist_ok=True)
        with open(_FEEDBACK_FILE, "a") as f:
            json.dump({"query": unmatched_query}, f)
            f.write("\n")
    except Exception as e:
        logger.error(f"Error storing feedback: {e}")
