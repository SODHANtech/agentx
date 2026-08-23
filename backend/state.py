from typing import TypedDict, Annotated, List, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentStep(TypedDict):
    id: str
    name: str
    status: str  # "waiting" | "running" | "completed"
    detail: str

# Custom reducer to append new agent steps to the existing execution log list
def add_agent_steps(left: List[AgentStep], right: Optional[List[AgentStep]]) -> List[AgentStep]:
    if not right:
        return left
    # Merge and update step list preserving unique step IDs
    merged = {step["id"]: step for step in (left + right)}
    return list(merged.values())

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_steps: Annotated[List[AgentStep], add_agent_steps]
    student_id: Optional[int]