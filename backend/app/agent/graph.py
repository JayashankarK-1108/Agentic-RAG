
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

class State(TypedDict, total=False):
    query: str
    department: Optional[str]
    steps: List[dict]
    response: str

def retrieve_node(state):
    steps = retrieve(state["query"], state.get("department"))
    return {"steps": steps}

def generate_node(state):
    steps = state["steps"]
    query = state["query"]

    if not steps:
        store_feedback(query)
        return {"response": "I could not find relevant information in the knowledge base for your query. Please try rephrasing your question."}

    # Build context from retrieved chunks
    context_parts = []
    for i, s in enumerate(steps, start=1):
        context_parts.append(f"[Context {i}]: {s['text']}")
    context = "\n\n".join(context_parts)

    # Call LLM with system prompt + retrieved context + user query
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Context from knowledge base:\n{context}\n\n"
            f"User question: {query}"
        )),
    ]
    llm_response = llm.invoke(messages)
    answer = llm_response.content

    # Only attach images if the answer references a process/procedure (not a greeting/chitchat)
    process_keywords = ["step", "click", "open", "go to", "navigate", "select", "enter",
                        "configure", "install", "enable", "disable", "set", "create",
                        "process", "follow", "procedure"]
    answer_lower = answer.lower()
    is_process_answer = any(kw in answer_lower for kw in process_keywords)

    if is_process_answer:
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
