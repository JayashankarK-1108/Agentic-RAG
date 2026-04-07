
import logging
from fastapi import FastAPI, HTTPException
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

class Query(BaseModel):
    query: str = Field(..., min_length=1, max_length=10000)
    department: str | None = Field(None, max_length=100)

@api.get("/")
def root():
    return {"status": "running"}

@api.post("/chat")
def chat(q: Query):
    try:
        result = app_graph.invoke({"query": q.query, "department": q.department})
        return {"response": result["response"]}
    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing your request")
