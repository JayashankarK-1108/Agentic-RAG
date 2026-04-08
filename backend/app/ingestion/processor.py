
def create_steps(pages):
    """
    Convert extracted pages into indexable steps.

    Each page is kept as a single chunk so the text-to-image association
    established during extraction is preserved. Steps shorter than 30
    characters (headings, blank lines, etc.) are skipped.
    """
    steps = []
    for p in pages:
        text = p["text"].strip()
        if len(text) >= 30:
            steps.append({"text": text, "images": p["images"]})
    return steps
