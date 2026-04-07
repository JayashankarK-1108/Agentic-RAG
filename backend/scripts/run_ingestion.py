
import glob
import os
import logging
from app.ingestion.multimodal_loader import extract_document
from app.ingestion.processor import create_steps
from app.ingestion.embedder import store_steps
from app.db.pinecone_client import clear_index, delete_by_source, get_index_stats

logging.basicConfig(level=logging.WARNING)

SEP  = "═" * 60
SEP2 = "─" * 60

# ── Ingestion mode ─────────────────────────────────────────
# INGESTION_MODE options:
#   clear_all   — wipe the entire index then re-ingest all PDFs (default, no duplicates)
#   per_source  — delete existing vectors per document before re-ingesting (Pinecone paid plan)
#   upsert_new  — only ingest, no deletion (use only for brand-new documents)
MODE = os.getenv("INGESTION_MODE", "clear_all").lower()

# ── Helpers ────────────────────────────────────────────────

def _print_header():
    mode_labels = {
        "clear_all":  "Clear All → Re-ingest",
        "per_source": "Per-Source Delete → Re-ingest",
        "upsert_new": "Upsert New Only",
    }
    print(f"\n{SEP}")
    print("  Agentic RAG — Ingestion Pipeline")
    print(f"  Mode : {mode_labels.get(MODE, MODE)}")
    print(SEP)

def _print_index_stats(label, stats):
    if stats:
        count = stats.get("total_vector_count", "unknown")
        print(f"\n  {label} vector count : {count}")

def _print_doc_stats(idx, total, source, pages, chunks, vectors, upserted,
                     img_found, img_uploaded, img_failed, deleted, status):
    ok = "✓" if status == "success" else "✗"
    img_st = (
        f"✓ {img_uploaded}/{img_found} uploaded"
        if img_failed == 0
        else f"⚠ {img_uploaded}/{img_found} uploaded, {img_failed} failed"
    )
    print(f"\n  [{idx}/{total}] {source}")
    print(f"  {SEP2}")
    if deleted is not None:
        del_label = "Existing vectors deleted"
        print(f"  {del_label:<28}: {'✓ Done' if deleted else '— Skipped'}")
    print(f"  {'Pages extracted':<28}: {pages}")
    print(f"  {'Chunks created':<28}: {chunks}")
    print(f"  {'Vectors embedded':<28}: {vectors}")
    print(f"  {'Upserted to Pinecone':<28}: {upserted}")
    print(f"  {'Images found':<28}: {img_found}")
    print(f"  {'Images uploaded to S3':<28}: {img_st}")
    print(f"  {'Status':<28}: {ok} {status.capitalize()}")

def _print_summary(doc_count, total_chunks, total_vectors, total_upserted,
                   total_img_found, total_img_uploaded, total_img_failed, errors):
    img_sum = (
        f"✓ {total_img_uploaded}/{total_img_found} uploaded"
        if total_img_failed == 0
        else f"⚠ {total_img_uploaded}/{total_img_found} uploaded, {total_img_failed} failed"
    )
    print(f"\n{SEP}")
    print("  SUMMARY")
    print(f"  {SEP2}")
    print(f"  {'Documents processed':<30}: {doc_count}")
    print(f"  {'Total chunks':<30}: {total_chunks}")
    print(f"  {'Total vectors embedded':<30}: {total_vectors}")
    print(f"  {'Total upserted to Pinecone':<30}: {total_upserted}")
    print(f"  {'Total images found':<30}: {total_img_found}")
    print(f"  {'Total images uploaded to S3':<30}: {img_sum}")
    if errors:
        print(f"  {'Errors':<30}: {errors} document(s) failed")
    print(f"  {'Final status':<30}: {'✓ Complete' if not errors else '⚠ Completed with errors'}")
    print(f"{SEP}\n")

# ── Main ───────────────────────────────────────────────────

_print_header()

pdf_dir   = os.path.join(os.path.dirname(__file__), "../../data/pdfs")
pdf_files = (
    glob.glob(os.path.join(pdf_dir, "*.pdf")) +
    glob.glob(os.path.join(pdf_dir, "*.docx"))
)

if not pdf_files:
    print(f"\n  ⚠  No documents found in: {pdf_dir}\n{SEP}\n")
else:
    # Show current index state before starting
    stats_before = get_index_stats()
    _print_index_stats("Index before ingestion", stats_before)

    # For clear_all mode: wipe the entire index once before processing any files
    if MODE == "clear_all":
        print(f"\n  Clearing index... ", end="", flush=True)
        clear_index()
        print("✓ Done")

    total_docs         = len(pdf_files)
    total_chunks       = 0
    total_vectors      = 0
    total_upserted     = 0
    total_img_found    = 0
    total_img_uploaded = 0
    total_img_failed   = 0
    errors             = 0

    for i, pdf_path in enumerate(pdf_files, start=1):
        source  = os.path.basename(pdf_path)
        deleted = None

        try:
            # For per_source mode: delete existing vectors for this document before re-ingesting
            if MODE == "per_source":
                print(f"\n  Deleting existing vectors for '{source}'... ", end="", flush=True)
                delete_by_source(source)
                deleted = True
                print("✓ Done")

            pages, img_stats = extract_document(pdf_path)
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
                             deleted=deleted,
                             status="success")
        except Exception as e:
            errors += 1
            _print_doc_stats(i, total_docs, source,
                             pages=0, chunks=0, vectors=0, upserted=0,
                             img_found=0, img_uploaded=0, img_failed=0,
                             deleted=deleted,
                             status=f"failed — {e}")

    _print_summary(total_docs, total_chunks, total_vectors, total_upserted,
                   total_img_found, total_img_uploaded, total_img_failed, errors)

    # Show final index state after ingestion
    stats_after = get_index_stats()
    _print_index_stats("Index after ingestion ", stats_after)
