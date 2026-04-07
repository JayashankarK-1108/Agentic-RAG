
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI
from app.agent.tools import retrieve, store_feedback

llm = ChatOpenAI(model="gpt-4o-mini")

class State(dict): pass

def retrieve_node(state):
    return {"steps": retrieve(state["query"], state.get("department"))}

def generate_node(state):
    steps = state["steps"]
    if not steps:
        store_feedback(state["query"])
        return {"response": "No relevant SOP found"}

    resp = ""
    for i, s in enumerate(steps):
        resp += f"\nStep {i+1}: {s['text']}\n"
        for img in s["images"]:
            if img:
                resp += f"Image: {img}\n"
    return {"response": resp}

graph = StateGraph(State)
graph.add_node("retrieve", retrieve_node)
graph.add_node("generate", generate_node)
graph.set_entry_point("retrieve")
graph.add_edge("retrieve", "generate")

app_graph = graph.compile()
