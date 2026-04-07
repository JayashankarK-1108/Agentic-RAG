
import fitz
from app.ingestion.s3_uploader import upload_image

def extract_pdf(file_path):
    try:
        doc = fitz.open(file_path)
        pages = []
        for pno, page in enumerate(doc):
            text = page.get_text()
            imgs = []
            for i, img in enumerate(page.get_images(full=True)):
                try:
                    xref = img[0]
                    base = doc.extract_image(xref)
                    url = upload_image(base["image"], f"p{pno}_{i}.png")
                    if url:
                        imgs.append(url)
                except Exception as e:
                    print(f"Error extracting image from page {pno}: {e}")
            pages.append({"text": text, "images": imgs})
        return pages
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return []
