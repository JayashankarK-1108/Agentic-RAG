
import re
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.agent.tools import retrieve, store_feedback

llm = ChatOpenAI(model="gpt-4o", temperature=0.2)

SYSTEM_PROMPT = """You are a helpful IT Knowledge Base Assistant that answers questions using the provided context.

Guidelines:
1. Rephrase and explain the context in your own words — do not copy text verbatim.
2. Always provide a COMPLETE answer — cover ALL steps, do not stop midway.
3. For each step, give enough detail so the user knows exactly what to click, where to look, and what to expect.
4. Keep your tone conversational and warm.
5. If the context is insufficient, say: "The provided context does not contain enough information to answer this question."
6. IMPORTANT — Images: Each context block may include one or more image URLs labelled "Screenshot:".
   When you write a numbered step, if that step's context block has a Screenshot URL, you MUST output
   it on its own line immediately after that step using EXACTLY this format (no changes):
   [SCREENSHOT: <url>]
   Example:
   1. Open Chrome and click the three-dot menu in the top-right corner, then select Settings.
   [SCREENSHOT: https://example.com/image.png]
   2. Scroll down and click Advanced.
   [SCREENSHOT: https://example.com/image2.png]
   If a context block has no screenshot, skip the tag for that step."""

CHITCHAT_PROMPT = """You are a friendly IT Knowledge Base Assistant.
Respond warmly to greetings and small talk in 1-2 sentences,
then let the user know you can help with IT processes and procedures."""

_CHITCHAT_PATTERNS = [
    "hello", "hi", "hey", "good morning", "good afternoon",
    "good evening", "good day", "how are you", "how r you",
    "my name is", "i am ", "i'm ", "thanks", "thank you",
    "bye", "goodbye", "see you", "take care", "nice to meet",
]

def _is_chitchat(text: str) -> bool:
    t = text.lower().strip()
    return len(t.split()) <= 15 and any(pat in t for pat in _CHITCHAT_PATTERNS)


class State(TypedDict, total=False):
    query: str
    department: Optional[str]
    history: List[dict]
    steps: List[dict]
    chitchat: bool
    response: str


def _build_history_messages(history: List[dict]) -> list:
    msgs = []
    for m in history:
        if m.get("role") == "user":
            msgs.append(HumanMessage(content=m["content"]))
        elif m.get("role") == "assistant":
            msgs.append(AIMessage(content=m["content"]))
    return msgs


def _build_context(steps: List[dict]) -> str:
    """
    Build context string with image URLs embedded per chunk so the LLM
    knows exactly which screenshot belongs to which piece of content.
    """
    parts = []
    for i, s in enumerate(steps, 1):
        block = f"[Context {i}]:\n{s['text']}"
        for url in s.get("images", []):
            if url:
                block += f"\nScreenshot: {url}"
        parts.append(block)
    return "\n\n".join(parts)


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
    history = state.get("history", [])

    # ── Greeting / small talk ──────────────────────────────────────
    if is_chitchat:
        messages = (
            [SystemMessage(content=CHITCHAT_PROMPT)]
            + _build_history_messages(history)
            + [HumanMessage(content=query)]
        )
        return {"response": llm.invoke(messages).content}

    # ── No relevant KB results ─────────────────────────────────────
    if not steps:
        store_feedback(query)
        return {"response": (
            "I could not find relevant information in the knowledge base for your query. "
            "Please try rephrasing your question or ask about a specific IT process."
        )}

    # ── Build context (with screenshot URLs embedded) and call LLM ─
    context = _build_context(steps)
    messages = (
        [SystemMessage(content=SYSTEM_PROMPT)]
        + _build_history_messages(history)
        + [HumanMessage(content=(
            f"Context from knowledge base:\n{context}\n\n"
            f"User question: {query}"
        ))]
    )
    answer = llm.invoke(messages).content

    # ── Convert [SCREENSHOT: url] → Image: url for frontend ───────
    answer = re.sub(r'\[SCREENSHOT:\s*(https?://[^\]]+)\]', r'Image: \1', answer)

    return {"response": answer}


graph = StateGraph(State)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")

app_graph = graph.compile()
