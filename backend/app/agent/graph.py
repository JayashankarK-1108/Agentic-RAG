
import re
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.tools import retrieve, store_feedback

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

SYSTEM_PROMPT = """You are a helpful assistant that answers questions using the provided context.

Guidelines:
1. Do not copy or paste text directly from the context.
2. Interpret and rephrase the information so it feels like a natural conversation.
3. Use the context as your source of truth, but explain it in your own words.
4. If the context is insufficient, say:
   "The provided context does not contain enough information to answer this question."
5. Always provide a COMPLETE answer — cover ALL steps from the context, do not stop midway.
6. For each step, provide enough detail so the user knows exactly what to do — mention where to click,
   what to look for, and any important notes or warnings. Keep the tone conversational and warm.
7. When your answer contains numbered steps, place one image marker on a new line immediately
   after EACH step — assign them in order: Step 1 gets [IMAGE_1], Step 2 gets [IMAGE_2], and so on.
   If there are more steps than images, reuse [IMAGE_1] after the last available marker.
   If there are no images available, skip this rule.
   Use the markers EXACTLY as shown — do not modify them."""

CHITCHAT_PROMPT = """You are a friendly IT Knowledge Base Assistant. \
Respond warmly to greetings and small talk in 1-2 sentences, \
then let the user know you can help with IT processes and procedures."""

# Patterns that indicate a greeting / small talk (not an IT query)
_CHITCHAT_PATTERNS = [
    "hello", "hi", "hey", "good morning", "good afternoon",
    "good evening", "good day", "how are you", "how r you",
    "my name is", "i am ", "i'm ", "thanks", "thank you",
    "bye", "goodbye", "see you", "take care", "nice to meet",
]

def _is_chitchat(text: str) -> bool:
    t = text.lower().strip()
    # Short messages (≤15 words) that match a greeting pattern
    return len(t.split()) <= 15 and any(pat in t for pat in _CHITCHAT_PATTERNS)


class State(TypedDict, total=False):
    query: str
    department: Optional[str]
    steps: List[dict]
    chitchat: bool
    response: str


def retrieve_node(state):
    query_text = state["query"]
    if _is_chitchat(query_text):
        return {"steps": [], "chitchat": True}
    steps = retrieve(query_text, state.get("department"))
    return {"steps": steps, "chitchat": False}


def generate_node(state):
    query = state["query"]
    steps = state.get("steps", [])
    is_chitchat = state.get("chitchat", False)

    # ── Greeting / small talk ──────────────────────────────────────
    if is_chitchat:
        messages = [
            SystemMessage(content=CHITCHAT_PROMPT),
            HumanMessage(content=query),
        ]
        return {"response": llm.invoke(messages).content}

    # ── No relevant KB results ─────────────────────────────────────
    if not steps:
        store_feedback(query)
        return {"response": (
            "I could not find relevant information in the knowledge base for your query. "
            "Please try rephrasing your question or ask about a specific IT process."
        )}

    # ── Build context and call LLM ─────────────────────────────────
    context = "\n\n".join(f"[Context {i}]: {s['text']}" for i, s in enumerate(steps, 1))
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Context from knowledge base:\n{context}\n\n"
            f"User question: {query}"
        )),
    ]
    answer = llm.invoke(messages).content

    # ── Collect ordered, unique image URLs from retrieved chunks ───
    seen = set()
    images = []
    for s in steps:
        for img in s.get("images", []):
            if img and img not in seen:
                seen.add(img)
                images.append(img)

    # ── Replace [IMAGE_N] markers with actual Image: <url> lines ───
    # The LLM places [IMAGE_1], [IMAGE_2] … after each step.
    # We map marker index → URL, cycling back to index 0 if there are
    # more markers than images (as instructed in the system prompt).
    if images:
        def replace_marker(m):
            n = int(m.group(1)) - 1          # [IMAGE_1] → index 0
            url = images[n % len(images)]
            return f"Image: {url}"
        answer = re.sub(r'\[IMAGE_(\d+)\]', replace_marker, answer)
    else:
        # No images available — strip any leftover markers
        answer = re.sub(r'\[IMAGE_\d+\]\n?', '', answer)

    return {"response": answer}


graph = StateGraph(State)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")

app_graph = graph.compile()
