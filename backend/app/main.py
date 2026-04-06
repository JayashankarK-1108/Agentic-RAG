
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from app.agent.graph import app_graph

api = FastAPI()

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Query(BaseModel):
    query: str
    department: str | None = None

@api.get("/")
def root():
    return {"status": "running"}

@api.post("/chat")
def chat(q: Query):
    result = app_graph.invoke({"query": q.query, "department": q.department})
    return {"response": result["response"]}
