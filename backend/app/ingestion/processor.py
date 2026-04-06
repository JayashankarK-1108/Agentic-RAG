
def create_steps(pages):
    steps = []
    for p in pages:
        for line in p["text"].split("\n"):
            if len(line.strip()) > 30:
                steps.append({"text": line.strip(), "images": p["images"]})
    return steps
