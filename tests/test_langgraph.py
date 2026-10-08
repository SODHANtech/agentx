import json
from langchain_core.messages import HumanMessage
from backend.graph import graph


def test_langgraph_nodes_registered():
    nodes = list(graph.nodes.keys())
    expected = [
        "__start__",
        "supervisor",
        "academic",
        "placement",
        "knowledge",
        "notification",
        "events",
        "services",
        "resume",
        "communication",
        "response"
    ]
    for n in expected:
        assert n in nodes


def test_langgraph_academic_execution():
    config = {"configurable": {"thread_id": "test_academic_thread"}}
    result = graph.invoke(
        {
            "messages": [HumanMessage(content="What are my Monday classes?")],
            "agent_steps": [],
            "student_id": 2
        },
        config=config
    )

    last_msg = result["messages"][-1].content
    data = json.loads(last_msg)
    assert "academic" in data
    assert isinstance(data["academic"], list)

    step_ids = [s["id"] for s in result["agent_steps"]]
    assert "supervisor" in step_ids
    assert "academic" in step_ids
    assert "response" in step_ids


def test_langgraph_placement_execution():
    config = {"configurable": {"thread_id": "test_placement_thread"}}
    result = graph.invoke(
        {
            "messages": [HumanMessage(content="Can I apply for Google?")],
            "agent_steps": [],
            "student_id": 2
        },
        config=config
    )

    last_msg = result["messages"][-1].content
    data = json.loads(last_msg)
    assert "placement" in data
    assert data["placement"]["status"] == "Eligible"
    assert data["placement"]["company"] == "Google"

    step_ids = [s["id"] for s in result["agent_steps"]]
    assert "supervisor" in step_ids
    assert "placement" in step_ids
    assert "rule_checker" in step_ids
    assert "response" in step_ids
