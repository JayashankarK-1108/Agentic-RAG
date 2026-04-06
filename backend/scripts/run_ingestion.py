
from app.ingestion.multimodal_loader import extract_pdf
from app.ingestion.processor import create_steps
from app.ingestion.embedder import store_steps

pages = extract_pdf("data/pdfs/sample.pdf")
steps = create_steps(pages)
store_steps(steps)

print("Ingestion done")
