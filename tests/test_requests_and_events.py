from datetime import datetime, timedelta
from backend.database import models


def test_student_request_lifecycle(client, student_headers, admin_headers, db_session):
    # 1. Student creates a new Bonafide Certificate request
    create_payload = {
        "type": "Bonafide Certificate",
        "details": "Required for passport verification"
    }
    res = client.post("/student/requests", json=create_payload, headers=student_headers)
    assert res.status_code == 200
    req_data = res.json()
    assert req_data["type"] == "Bonafide Certificate"
    assert req_data["status"] == "Pending"
    request_id = req_data["id"]

    # 2. Student views their requests list
    list_res = client.get("/student/requests", headers=student_headers)
    assert list_res.status_code == 200
    requests = list_res.json()
    assert any(r["id"] == request_id for r in requests)

    # 3. Admin retrieves and reviews the request
    admin_get_res = client.get(f"/admin/requests/{request_id}", headers=admin_headers)
    assert admin_get_res.status_code == 200
    assert admin_get_res.json()["id"] == request_id

    # 4. Admin updates status to Approved with note
    update_payload = {
        "status": "Approved",
        "note": "Verified student records and granted certificate"
    }
    update_res = client.put(f"/admin/requests/{request_id}", json=update_payload, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "success"

    # Verify request status changed in database
    verified_res = client.get(f"/admin/requests/{request_id}", headers=admin_headers)
    assert verified_res.status_code == 200
    assert verified_res.json()["status"] == "Approved"

    # 5. Check request history timeline
    history_res = client.get(f"/student/requests/{request_id}/history", headers=student_headers)
    assert history_res.status_code == 200
    history_items = history_res.json()
    assert len(history_items) >= 1
    assert history_items[-1]["new_status"] == "Approved"


def test_unified_events_and_registrations(client, student_headers, admin_headers):
    # 1. Admin creates a new event
    start_time = (datetime.utcnow() + timedelta(days=2)).isoformat()
    end_time = (datetime.utcnow() + timedelta(days=2, hours=4)).isoformat()
    event_payload = {
        "title": "Hackathon 2026",
        "category": "Hackathon",
        "description": "Annual 24-hour campus coding challenge",
        "venue": "Innovation Hub, Block C",
        "start_datetime": start_time,
        "end_datetime": end_time,
        "max_participants": 50,
        "published": True
    }
    create_res = client.post("/admin/events", json=event_payload, headers=admin_headers)
    assert create_res.status_code == 200
    event_id = create_res.json()["id"]

    # 2. Public / Student lists published events
    events_res = client.get("/events")
    assert events_res.status_code == 200
    events = events_res.json()
    assert any(e["id"] == event_id for e in events)

    # 3. Student registers for the event
    reg_res = client.post(f"/events/{event_id}/register", headers=student_headers)
    assert reg_res.status_code == 200
    assert reg_res.json()["status"] == "success"

    # 4. Student verifies their registration list
    my_regs_res = client.get("/student/event-registrations", headers=student_headers)
    assert my_regs_res.status_code == 200
    reg_items = my_regs_res.json()
    assert any(r["event_id"] == event_id for r in reg_items)

    # 5. Student cancels registration
    cancel_res = client.delete(f"/events/{event_id}/register", headers=student_headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "success"

    # 6. REGRESSION TEST: Student re-registers for the event after cancellation (DEFECT-P2-01)
    re_reg_res = client.post(f"/events/{event_id}/register", headers=student_headers)
    assert re_reg_res.status_code == 200, f"Re-registration failed: {re_reg_res.text}"
    assert re_reg_res.json()["status"] == "success"

    # 7. Verify database state is correctly "Registered"
    my_regs_after = client.get("/student/event-registrations", headers=student_headers)
    assert my_regs_after.status_code == 200
    matching_reg = next((r for r in my_regs_after.json() if r["event_id"] == event_id), None)
    assert matching_reg is not None
    assert matching_reg["status"] == "Registered"

    # 8. Prevent duplicate active registration
    dup_res = client.post(f"/events/{event_id}/register", headers=student_headers)
    assert dup_res.status_code == 400
    assert "already registered" in dup_res.json()["detail"].lower()
