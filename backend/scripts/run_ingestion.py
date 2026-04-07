
import glob
import os
import logging
from app.ingestion.multimodal_loader import extract_pdf
from app.ingestion.processor import create_steps
from app.ingestion.embedder import store_steps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pdf_dir = os.path.join(os.path.dirname(__file__), "../../data/pdfs")
pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

if not pdf_files:
    logger.warning(f"No PDF files found in {pdf_dir}")
else:
    for pdf_path in pdf_files:
        source = os.path.basename(pdf_path)
        logger.info(f"Ingesting: {source}")
        pages = extract_pdf(pdf_path)
        steps = create_steps(pages)
        store_steps(steps, source=source)
        logger.info(f"Done: {source} — {len(steps)} steps stored")

logger.info("Ingestion complete")
