
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
3. YOU MUST format every procedural step as a numbered list: 1. 2. 3. etc.
   NEVER use bold headings or bullet points for steps — only numbered format.
   Example of correct format:
   1. Open Chrome and click the three-dot menu in the top-right corner, then select Settings.
   2. In the search bar at the top of Settings, type PROXY and click Open proxy settings.
   3. Click LAN Settings in the dialog that appears.
4. For each step, give enough detail: what to click, where to look, what to expect.
5. Keep your tone conversational and warm.
6. If the context is insufficient, say: "The provided context does not contain enough information to answer this question."
7. Do NOT include any image links or screenshot references — the system handles images separately."""

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


def _inject_images_after_steps(answer: str, steps: List[dict]) -> str:
    """
    Collect all images from retrieved steps in order, then inject them
    after each paragraph/step block in the answer — independent of how
    the LLM chose to format the response.
    """
    # Collect unique image URLs in order from retrieved chunks
    seen = set()
    images = []
    for s in steps:
        for url in s.get("images", []):
            if url and url not in seen:
                seen.add(url)
                images.append(url)

    if not images:
        return answer

    # Split by any newline (LLM may use single or double newlines between steps)
    lines = answer.split("\n")
    result = []
    img_index = 0

    for line in lines:
        result.append(line)
        stripped = line.strip()
        # Inject after any substantive line (a real step, not blank or short intro)
        is_step = (
            len(stripped) > 30 and
            not stripped.endswith(":")  # skip intro lines like "Follow these steps:"
        )
        if is_step and img_index < len(images):
            result.append(f"\nImage: {images[img_index]}\n")
            img_index += 1

    return "\n".join(result)


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

    # ── Build context and call LLM (no image instructions) ─────────
    context = "\n\n".join(f"[Context {i}]:\n{s['text']}" for i, s in enumerate(steps, 1))
    messages = (
        [SystemMessage(content=SYSTEM_PROMPT)]
        + _build_history_messages(history)
        + [HumanMessage(content=(
            f"Context from knowledge base:\n{context}\n\n"
            f"User question: {query}"
        ))]
    )
    answer = llm.invoke(messages).content

    # ── Inject images after numbered steps (backend-controlled) ────
    answer = _inject_images_after_steps(answer, steps)

    return {"response": answer}


graph = StateGraph(State)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")

app_graph = graph.compile()
