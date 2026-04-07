
import os
import zipfile
import fitz
from docx import Document
from docx.oxml.ns import qn
from app.ingestion.s3_uploader import upload_image


# ── PDF extraction ─────────────────────────────────────────

def extract_pdf(file_path):
    """
    Extract text and images from a PDF file.
    Images are uploaded to S3 and their URLs stored with the page they appear on.

    Returns:
        pages      : list of {text, images}
        image_stats: {found, uploaded, failed}
    """
    try:
        source = os.path.basename(file_path)   # e.g. "Proxy_Process.pdf"
        doc = fitz.open(file_path)
        pages = []
        found = uploaded = failed = 0

        for pno, page in enumerate(doc):
            text = page.get_text()
            imgs = []
            for i, img in enumerate(page.get_images(full=True)):
                found += 1
                try:
                    xref = img[0]
                    base = doc.extract_image(xref)
                    url = upload_image(base["image"], f"p{pno}_{i}.png", source=source)
                    if url:
                        imgs.append(url)
                        uploaded += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    print(f"Error extracting image from page {pno}: {e}")
            pages.append({"text": text, "images": imgs})

        return pages, {"found": found, "uploaded": uploaded, "failed": failed}
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return [], {"found": 0, "uploaded": 0, "failed": 0}


# ── DOCX extraction ────────────────────────────────────────

def _upload_docx_images(file_path):
    """
    Pre-upload every image inside the DOCX zip (word/media/*) to S3.
    Returns a dict mapping relationship ID → S3 URL.
    """
    rel_to_url = {}
    found = uploaded = failed = 0
    source = os.path.basename(file_path)   # e.g. "WLAN_Process.docx"

    try:
        doc = Document(file_path)

        # Build rId → (filename, raw bytes) from the document's relationships
        with zipfile.ZipFile(file_path) as zf:
            media = {os.path.basename(n): zf.read(n)
                     for n in zf.namelist() if n.startswith("word/media/")}

        for rid, rel in doc.part.rels.items():
            if "image" not in rel.reltype:
                continue
            img_name = os.path.basename(rel.target_ref)
            img_data = media.get(img_name)
            if img_data is None:
                continue
            found += 1
            url = upload_image(img_data, img_name, source=source)
            if url:
                rel_to_url[rid] = url
                uploaded += 1
            else:
                failed += 1

    except Exception as e:
        print(f"Error uploading DOCX images: {e}")

    return rel_to_url, {"found": found, "uploaded": uploaded, "failed": failed}


def _get_paragraph_image_rids(para):
    """Return relationship IDs for all inline images inside a paragraph."""
    rids = []
    for blip in para._element.iter(qn("a:blip")):
        rid = blip.get(qn("r:embed"))
        if rid:
            rids.append(rid)
    return rids


def extract_docx(file_path):
    """
    Extract text and images from a DOCX file.
    Images are uploaded to S3 and associated with the section they appear in.
    Sections are split on Heading-style paragraphs.

    Returns:
        pages      : list of {text, images}
        image_stats: {found, uploaded, failed}
    """
    try:
        rel_to_url, img_stats = _upload_docx_images(file_path)
        doc = Document(file_path)

        pages = []
        section_lines  = []
        section_images = []

        def flush_section():
            if section_lines:
                pages.append({
                    "text":   "\n".join(section_lines),
                    "images": list(section_images)
                })

        for para in doc.paragraphs:
            # New heading → flush the previous section and start fresh
            if para.style.name.startswith("Heading"):
                flush_section()
                section_lines  = []
                section_images = []

            text = para.text.strip()
            if text:
                section_lines.append(text)

            # Collect images that appear in this paragraph
            for rid in _get_paragraph_image_rids(para):
                url = rel_to_url.get(rid)
                if url and url not in section_images:
                    section_images.append(url)

        # Also extract text from tables (attach all doc images to table rows)
        all_urls = list(rel_to_url.values())
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(
                    cell.text.strip() for cell in row.cells if cell.text.strip()
                )
                if row_text:
                    pages.append({"text": row_text, "images": all_urls})

        flush_section()
        return pages, img_stats

    except Exception as e:
        print(f"Error extracting DOCX: {e}")
        return [], {"found": 0, "uploaded": 0, "failed": 0}


# ── Universal entry point ──────────────────────────────────

def extract_document(file_path):
    """Auto-detect file type and extract text + images."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_docx(file_path)
    else:
        print(f"Unsupported file type: {ext}")
        return [], {"found": 0, "uploaded": 0, "failed": 0}
