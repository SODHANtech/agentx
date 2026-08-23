from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.state import AgentState
from backend.nodes import router_node

builder = StateGraph(AgentState)

builder.add_node("router", router_node)

builder.add_edge(START, "router")
builder.add_edge("router", END)

memory = MemorySaver()

graph = builder.compile(
    checkpointer=memory
)