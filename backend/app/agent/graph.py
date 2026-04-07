
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.tools import retrieve, store_feedback

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

SYSTEM_PROMPT = """You are a helpful IT Knowledge Base Assistant. \
Your job is to answer user questions about IT processes and procedures \
using only the context retrieved from the knowledge base.

Guidelines:
- Answer clearly and concisely based on the provided context.
- Use numbered steps when explaining a process.
- If the context does not contain enough information, say so honestly.
- Do not make up information not present in the context.
- Keep your response focused and practical."""

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

    # ── Attach unique images from retrieved chunks ─────────────────
    seen = set()
    image_lines = []
    for s in steps:
        for img in s.get("images", []):
            if img and img not in seen:
                seen.add(img)
                image_lines.append(f"Image: {img}")
    if image_lines:
        answer += "\n\n" + "\n".join(image_lines)

    return {"response": answer}


graph = StateGraph(State)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")

app_graph = graph.compile()
