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
        return left or []
    # If a reset signal is present, discard historical turn steps
    if any(step.get("_reset") for step in right):
        cleaned = [{k: v for k, v in step.items() if k != "_reset"} for step in right]
        merged = {step["id"]: step for step in cleaned}
        return list(merged.values())
    merged = {step["id"]: step for step in (left or []) + right}
    return list(merged.values())

def merge_dict(left: Optional[dict], right: Optional[dict]) -> dict:
    if right is not None and right.get("_reset") is True:
        clean = dict(right)
        clean.pop("_reset", None)
        return clean
    res = dict(left or {})
    if right:
        res.update(right)
    return res

class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_steps: Annotated[List[AgentStep], add_agent_steps]
    student_id: Optional[int]
    pending_agents: List[str]
    params: dict
    agent_outputs: Annotated[dict, merge_dict]