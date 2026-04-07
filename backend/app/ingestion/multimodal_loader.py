
import fitz
from app.ingestion.s3_uploader import upload_image

def extract_pdf(file_path):
    """
    Returns:
        pages      : list of {text, images}
        image_stats: {found, uploaded, failed}
    """
    try:
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
                    url = upload_image(base["image"], f"p{pno}_{i}.png")
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
