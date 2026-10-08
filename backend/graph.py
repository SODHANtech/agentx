from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.state import AgentState
from backend.nodes import (
    supervisor_node,
    academic_node,
    placement_node,
    knowledge_node,
    notification_node,
    events_node,
    services_node,
    resume_node,
    communication_node,
    response_node,
    route_next_agent
)

# Initialize LangGraph state graph
builder = StateGraph(AgentState)

# Register all discrete, specialized campus agent nodes
builder.add_node("supervisor", supervisor_node)
builder.add_node("academic", academic_node)
builder.add_node("placement", placement_node)
builder.add_node("knowledge", knowledge_node)
builder.add_node("notification", notification_node)
builder.add_node("events", events_node)
builder.add_node("services", services_node)
builder.add_node("resume", resume_node)
builder.add_node("communication", communication_node)
builder.add_node("response", response_node)

# Flow: START -> supervisor
builder.add_edge(START, "supervisor")

# Routing mapping for dynamic conditional transitions
node_destinations = {
    "academic": "academic",
    "placement": "placement",
    "knowledge": "knowledge",
    "notification": "notification",
    "events": "events",
    "services": "services",
    "resume": "resume",
    "communication": "communication",
    "response": "response"
}

# Conditional routing from supervisor
builder.add_conditional_edges("supervisor", route_next_agent, node_destinations)

# After each specialized node runs, loop back to route_next_agent to service multi-agent requests
for agent_node in [
    "academic",
    "placement",
    "knowledge",
    "notification",
    "events",
    "services",
    "resume",
    "communication"
]:
    builder.add_conditional_edges(agent_node, route_next_agent, node_destinations)

# Final formatting exit
builder.add_edge("response", END)

memory = MemorySaver()

# Compile the production LangGraph state graph
graph = builder.compile(
    checkpointer=memory
)