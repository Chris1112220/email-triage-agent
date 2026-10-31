from langgraph.graph import StateGraph, START, END
from app.state import EmailState
from app.nodes import classify, label, draft, approve

builder = StateGraph(EmailState)
builder.add_node("classify", classify)
builder.add_node("label", label)
builder.add_node("draft", draft)
builder.add_node("approve", approve)

builder.add_edge(START, "classify")
builder.add_edge("classify", "label")
builder.add_edge("label", "draft")
builder.add_edge("draft", "approve")
builder.add_edge("approve", END)

graph = builder.compile()