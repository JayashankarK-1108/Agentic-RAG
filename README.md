
# Full Production Agentic Multimodal RAG

## Features
- SOP chatbot
- Image extraction + S3 storage
- Pinecone vector search
- LangGraph agent
- React UI

## Run Backend
pip install -r backend/requirements.txt
uvicorn backend.app.main:api --reload

## Ingestion
python backend/scripts/run_ingestion.py

## Frontend
cd frontend
npm install
npm start
