
import logging
import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
from app.agent.graph import app_graph

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str = Field(..., max_length=10000)

class Query(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    department: str | None = Field(None, max_length=100)
    history: list[ChatMessage] = Field(default_factory=list)

@api.get("/health")
def health():
    return {"status": "running"}

@api.get("/image-proxy")
async def image_proxy(url: str):
    """Proxy S3 presigned images through the backend to avoid ad-blocker blocks."""
    if not url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid URL")
    async with httpx.AsyncClient(follow_redirects=True) as client:
        r = await client.get(url)
        if r.status_code != 200:
            raise HTTPException(status_code=r.status_code, detail="Image fetch failed")
        return StreamingResponse(
            iter([r.content]),
            media_type=r.headers.get("content-type", "image/png"),
        )

@api.post("/chat")
def chat(q: Query):
    try:
        history = [{"role": m.role, "content": m.content} for m in q.history]
        result = app_graph.invoke({
            "query": q.query,
            "department": q.department,
            "history": history,
        })
        return {"response": result["response"]}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve frontend static files — must be mounted LAST so API routes take priority
_frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.isdir(_frontend_dir):
    logger.info(f"Serving frontend from: {_frontend_dir}")
    api.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at: {_frontend_dir}")
