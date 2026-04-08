
import logging
from langchain_openai import OpenAIEmbeddings
from app.db.pinecone_client import upsert

logger = logging.getLogger(__name__)
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

def store_steps(steps, source="unknown"):
    vectors = []
    for i, s in enumerate(steps):
        emb = embedder.embed_query(s["text"])
        vectors.append({
            "id": f"{source}-{i}",          # e.g. WLAN_Process.docx-0
            "values": emb,
            "metadata": {
                "text":        s["text"],
                "image_urls":  s.get("images", []),
                "image_order": "positioned",
                "page":        i,
                "source":      source,
            }
        })
    upserted_count = upsert(vectors)
    logger.info(f"Stored {len(vectors)} vectors from source: {source}")
    return {"vectors": len(vectors), "upserted": upserted_count}
