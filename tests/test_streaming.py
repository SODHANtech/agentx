import json


def test_standard_ask_endpoint(client, student_headers):
    response = client.get(
        "/ask",
        params={"query": "What are my Monday classes?"},
        headers=student_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "Timetable Classes:" in data["response"] or "Artificial Intelligence" in data["response"]
    assert len(data["agent_steps"]) >= 2


def test_streaming_ask_endpoint(client, student_headers):
    with client.stream(
        "GET",
        "/ask/stream",
        params={"query": "What are my Monday classes?"},
        headers=student_headers
    ) as stream_response:
        assert stream_response.status_code == 200
        assert "text/event-stream" in stream_response.headers.get("content-type", "")

        events = []
        for line in stream_response.iter_lines():
            if line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                events.append(payload)

        assert len(events) >= 2
        event_types = [e["type"] for e in events]
        assert "start" in event_types
        assert "complete" in event_types

        # Complete event contains final response
        complete_event = next(e for e in events if e["type"] == "complete")
        assert complete_event["status"] == "success"
        assert len(complete_event["agent_steps"]) >= 2


def test_ai_rate_limiter_allows_15_and_blocks_16th():
    from backend.core.rate_limit import ai_limiter
    assert ai_limiter.requests_limit == 15
    test_key = "test_rate_limit_unit_key"
    ai_limiter.history[test_key] = []
    
    for i in range(15):
        assert ai_limiter.is_rate_limited(test_key) is False, f"Blocked prematurely on request {i+1}"
        
    assert ai_limiter.is_rate_limited(test_key) is True
