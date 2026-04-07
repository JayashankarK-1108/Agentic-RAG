
import glob
import os
import logging
from app.ingestion.multimodal_loader import extract_pdf
from app.ingestion.processor import create_steps
from app.ingestion.embedder import store_steps

logging.basicConfig(level=logging.WARNING)  # suppress library noise
logger = logging.getLogger(__name__)

SEP  = "═" * 56
SEP2 = "─" * 56

def _print_header():
    print(f"\n{SEP}")
    print("  Agentic RAG — Ingestion Pipeline")
    print(SEP)

def _print_doc_stats(index, total, source, pages, chunks, vectors, upserted,
                     img_found, img_uploaded, img_failed, status):
    ok = "✓" if status == "success" else "✗"
    img_status = (
        f"✓ {img_uploaded}/{img_found} uploaded"
        if img_failed == 0
        else f"⚠ {img_uploaded}/{img_found} uploaded, {img_failed} failed"
    )
    print(f"\n  [{index}/{total}] {source}")
    print(f"  {SEP2}")
    print(f"  {'Pages extracted':<26}: {pages}")
    print(f"  {'Chunks created':<26}: {chunks}")
    print(f"  {'Vectors embedded':<26}: {vectors}")
    print(f"  {'Upserted to Pinecone':<26}: {upserted}")
    print(f"  {'Images found':<26}: {img_found}")
    print(f"  {'Images uploaded to S3':<26}: {img_status}")
    print(f"  {'Status':<26}: {ok} {status.capitalize()}")

def _print_summary(doc_count, total_chunks, total_vectors, total_upserted,
                   total_img_found, total_img_uploaded, total_img_failed, errors):
    img_summary = (
        f"✓ {total_img_uploaded}/{total_img_found} uploaded"
        if total_img_failed == 0
        else f"⚠ {total_img_uploaded}/{total_img_found} uploaded, {total_img_failed} failed"
    )
    print(f"\n{SEP}")
    print("  SUMMARY")
    print(f"  {SEP2}")
    print(f"  {'Documents processed':<28}: {doc_count}")
    print(f"  {'Total chunks':<28}: {total_chunks}")
    print(f"  {'Total vectors embedded':<28}: {total_vectors}")
    print(f"  {'Total upserted to Pinecone':<28}: {total_upserted}")
    print(f"  {'Total images found':<28}: {total_img_found}")
    print(f"  {'Total images uploaded to S3':<28}: {img_summary}")
    if errors:
        print(f"  {'Errors':<28}: {errors} document(s) failed")
    print(f"  {'Final status':<28}: {'✓ Complete' if not errors else '⚠ Completed with errors'}")
    print(f"{SEP}\n")

# ── Main ──────────────────────────────────────────────

_print_header()

pdf_dir   = os.path.join(os.path.dirname(__file__), "../../data/pdfs")
pdf_files = glob.glob(os.path.join(pdf_dir, "*.pdf"))

if not pdf_files:
    print(f"\n  ⚠  No PDF files found in: {pdf_dir}\n{SEP}\n")
else:
    total_docs         = len(pdf_files)
    total_chunks       = 0
    total_vectors      = 0
    total_upserted     = 0
    total_img_found    = 0
    total_img_uploaded = 0
    total_img_failed   = 0
    errors             = 0

    for i, pdf_path in enumerate(pdf_files, start=1):
        source = os.path.basename(pdf_path)
        try:
            pages, img_stats = extract_pdf(pdf_path)
            steps            = create_steps(pages)
            result           = store_steps(steps, source=source)

            doc_vectors  = result["vectors"]
            doc_upserted = result["upserted"]

            total_chunks       += len(steps)
            total_vectors      += doc_vectors
            total_upserted     += doc_upserted
            total_img_found    += img_stats["found"]
            total_img_uploaded += img_stats["uploaded"]
            total_img_failed   += img_stats["failed"]

            _print_doc_stats(i, total_docs, source,
                             pages=len(pages),
                             chunks=len(steps),
                             vectors=doc_vectors,
                             upserted=doc_upserted,
                             img_found=img_stats["found"],
                             img_uploaded=img_stats["uploaded"],
                             img_failed=img_stats["failed"],
                             status="success")
        except Exception as e:
            errors += 1
            _print_doc_stats(i, total_docs, source,
                             pages=0, chunks=0, vectors=0, upserted=0,
                             img_found=0, img_uploaded=0, img_failed=0,
                             status=f"failed — {e}")

    _print_summary(total_docs, total_chunks, total_vectors, total_upserted,
                   total_img_found, total_img_uploaded, total_img_failed, errors)
