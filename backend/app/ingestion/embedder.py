
import uuid
import logging
from langchain_openai import OpenAIEmbeddings
from app.db.pinecone_client import upsert

logger = logging.getLogger(__name__)
embedder = OpenAIEmbeddings()

def store_steps(steps, source="unknown"):
    vectors = []
    for s in steps:
        emb = embedder.embed_query(s["text"])
        vectors.append({
            "id": str(uuid.uuid4()),
            "values": emb,
            "metadata": {"text": s["text"], "images": s["images"], "source": source}
        })
    upsert(vectors)
    logger.info(f"Stored {len(vectors)} vectors from source: {source}")
