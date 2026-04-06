
import json
from langchain_openai import OpenAIEmbeddings
from app.db.pinecone_client import query

embedder = OpenAIEmbeddings()

def retrieve(query_text, department=None):
    try:
        emb = embedder.embed_query(query_text)
        results = query(emb)
        return [{"text": m["metadata"]["text"], "images": m["metadata"].get("images", [])}
                for m in results.get("matches", [])]
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []

def store_feedback(query):
    with open("backend/app/db/feedback.json", "a") as f:
        json.dump({"query": query}, f)
        f.write("\n")
