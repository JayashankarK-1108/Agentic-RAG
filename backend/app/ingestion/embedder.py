
from langchain_openai import OpenAIEmbeddings
from app.db.pinecone_client import upsert

embedder = OpenAIEmbeddings()

def store_steps(steps):
    vectors = []
    for i, s in enumerate(steps):
        emb = embedder.embed_query(s["text"])
        vectors.append({
            "id": f"step-{i}",
            "values": emb,
            "metadata": {"text": s["text"], "images": s["images"]}
        })
    upsert(vectors)
