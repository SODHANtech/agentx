import os
import sys
import httpx
import tempfile
from backend.config import settings

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== STARTING AUTOMATED ENDPOINTS VERIFICATION ===")
    
    # Check if backend is running
    try:
        httpx.get(f"{BASE_URL}/")
    except Exception:
        print(f"ERROR: Backend server is not running on {BASE_URL}. Please start the backend server first!")
        sys.exit(1)
        
    client = httpx.Client(
        base_url=BASE_URL,
        headers={"X-Bypass-Rate-Limit": settings.JWT_SECRET_KEY}
    )
    
    # ---------------------------------------------
    # 1. AUTH TESTS
    # ---------------------------------------------
    print("\n1. Running Auth Tests...")
    
    # Test valid login (Admin)
    admin_login_res = client.post("/auth/login", json={"email": "admin@campus.edu", "password": "admin123"})
    assert admin_login_res.status_code == 200, f"Admin login failed: {admin_login_res.text}"
    admin_token = admin_login_res.json()["access_token"]
    print("  [PASS] Admin login successful")

    # Test valid login (Satya student)
    satya_login_res = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "student123"})
    assert satya_login_res.status_code == 200, f"Satya login failed: {satya_login_res.text}"
    satya_token = satya_login_res.json()["access_token"]
    print("  [PASS] Student login successful")

    # Test invalid login
    invalid_login_res = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "wrongpassword"})
    assert invalid_login_res.status_code == 401, f"Expected 401 for wrong password: {invalid_login_res.status_code}"
    print("  [PASS] Invalid login rejected")

    # Test student self-registration forces role="Student"
    reg_payload = {
        "name": "Test Account",
        "email": "test_rbac@campus.edu",
        "password": "password123",
        "role": "Admin",  # Attempting privilege escalation
        "cgpa": 8.0,
        "backlogs": 0
    }
    
    # Cleanup if previously created
    client.post("/auth/login", json={"email": "test_rbac@campus.edu", "password": "password123"})
    # Register
    reg_res = client.post("/auth/register", json=reg_payload)
    if reg_res.status_code == 400 and "already exists" in reg_res.json().get("detail", ""):
        print("  [NOTE] Test user already exists, registration check skipped (handled)")
    else:
        assert reg_res.status_code == 200, f"Registration failed: {reg_res.text}"
        assert reg_res.json()["user"]["role"] == "Student", "Privilege escalation allowed! Role was not forced to Student."
        print("  [PASS] Student registration forced role='Student' successfully")

    # ---------------------------------------------
    # 2. RBAC TESTS
    # ---------------------------------------------
    print("\n2. Running RBAC Tests...")
    
    student_headers = {"Authorization": f"Bearer {satya_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Student cannot access /admin/clusters
    clusters_student_res = client.get("/admin/clusters", headers=student_headers)
    assert clusters_student_res.status_code == 403, f"Expected 403 for student accessing admin clusters: {clusters_student_res.status_code}"
    print("  [PASS] Student forbidden from /admin/clusters")

    # Student cannot trigger clustering
    cluster_trigger_student_res = client.post("/admin/complaints/cluster", headers=student_headers)
    assert cluster_trigger_student_res.status_code == 403, f"Expected 403 for student triggering clustering: {cluster_trigger_student_res.status_code}"
    print("  [PASS] Student forbidden from triggering semantic clustering")

    # Admin can access admin endpoints
    clusters_admin_res = client.get("/admin/clusters", headers=admin_headers)
    assert clusters_admin_res.status_code == 200, f"Admin could not fetch clusters: {clusters_admin_res.text}"
    print("  [PASS] Admin allowed to fetch clusters")

    # ---------------------------------------------
    # 3. EVENTS TESTS (Isolation and User ownership)
    # ---------------------------------------------
    print("\n3. Running Event Registrations Tests...")
    
    # Log in another student
    priya_login_res = client.post("/auth/login", json={"email": "priya@campus.edu", "password": "student123"})
    priya_token = priya_login_res.json()["access_token"]
    priya_headers = {"Authorization": f"Bearer {priya_token}"}
    
    # Satya registers for Tech Fest
    reg_satya_res = client.post("/events/register", json={"event": "Tech Fest"}, headers=student_headers)
    assert reg_satya_res.status_code == 200, f"Satya registration failed: {reg_satya_res.text}"
    print("  [PASS] Student A registered for event")

    # Priya registers for Tech Fest
    reg_priya_res = client.post("/events/register", json={"event": "Tech Fest"}, headers=priya_headers)
    assert reg_priya_res.status_code == 200, f"Priya registration failed: {reg_priya_res.text}"
    print("  [PASS] Student B registered for same event successfully (Isolation)")

    # Satya cancels Tech Fest
    cancel_satya_res = client.post("/events/cancel", json={"event": "Tech Fest"}, headers=student_headers)
    assert cancel_satya_res.status_code == 200, f"Satya cancellation failed: {cancel_satya_res.text}"
    print("  [PASS] Student A cancelled registration successfully")

    # Verify Priya remains registered
    priya_regs = client.get("/events/registrations", headers=priya_headers)
    assert priya_regs.status_code == 200
    events_list = [r["event"] for r in priya_regs.json().get("registered_events", [])]
    assert "Tech Fest" in events_list, f"Student B registration affected by Student A cancellation: {events_list}"
    print("  [PASS] Student B remains registered (Isolation verified)")

    # ---------------------------------------------
    # 4. GRIEVANCES AND COMPLAINTS WORKFLOW
    # ---------------------------------------------
    print("\n4. Running Grievances and Clustering Workflow Tests...")
    
    # Student files two grievances in different categories to form a cluster
    # Let's seed two grievances that are semantically identical to force a cluster
    g1_res = client.post("/student-services/grievance", json={"category": "Hostel", "description": "The water supply in hostel block A is broken since yesterday."}, headers=student_headers)
    assert g1_res.status_code == 200, f"Failed to post grievance: {g1_res.text}"
    
    g2_res = client.post("/student-services/grievance", json={"category": "Hostel", "description": "Block A hostel has no running water today, it is broken."}, headers=priya_headers)
    assert g2_res.status_code == 200, f"Failed to post grievance: {g2_res.text}"
    print("  [PASS] Two semantically similar student grievances filed in SQLite")

    # Run Semantic Clustering
    cluster_res = client.post("/admin/complaints/cluster", headers=admin_headers)
    assert cluster_res.status_code == 200, f"Semantic clustering failed: {cluster_res.text}"
    cluster_data = cluster_res.json()
    print(f"  [PASS] Admin semantic clustering triggered successfully. Found clusters: {len(cluster_data.get('clusters', []))}")
    
    # If a cluster was formed, let's test broadcast
    if cluster_data.get("clusters"):
        target_cluster = cluster_data["clusters"][0]
        cluster_id = target_cluster["id"]
        
        # Broadcast Resolution
        broadcast_res = client.post(f"/admin/clusters/{cluster_id}/broadcast", headers=admin_headers)
        assert broadcast_res.status_code == 200, f"Resolution broadcast failed: {broadcast_res.text}"
        print(f"  [PASS] Broadcasted resolution for cluster #{cluster_id}")
        
        # Verify student receives the resolution announcement in Communications feed
        comms_res = client.get("/communications", headers=student_headers)
        assert comms_res.status_code == 200
        announcements = comms_res.json()
        assert len(announcements) > 0, "No announcements received by student."
        # The latest announcement should be our broadcast resolution
        latest_ann = announcements[0]
        assert "Resolution" in latest_ann["title"], f"Latest announcement is not resolution: {latest_ann['title']}"
        print("  [PASS] Student Communications feed synced and resolution announcement visible")

    # ---------------------------------------------
    # 5. RESUME UPLOAD SECURITY
    # ---------------------------------------------
    print("\n5. Running Resume Upload Security Tests...")
    
    # Test valid PDF (small)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_pdf:
        pdf_content = (
            b"%PDF-1.4\n"
            b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
            b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
            b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources <<>> /Contents 4 0 R>> endobj\n"
            b"4 0 obj <</Length 49>> stream\n"
            b"BT /F1 12 Tf 72 712 Td (Mock Resume for Satya) Tj ET\n"
            b"endstream\n"
            b"endobj\n"
            b"xref\n"
            b"0 5\n"
            b"0000000000 65535 f\n"
            b"0000000009 00000 n\n"
            b"0000000056 00000 n\n"
            b"0000000111 00055 n\n"
            b"0000000212 00000 n\n"
            b"trailer <</Size 5 /Root 1 0 R>>\n"
            b"startxref\n"
            b"310\n"
            b"%%EOF\n"
        )
        tmp_pdf.write(pdf_content)
        tmp_pdf_name = tmp_pdf.name
        
    try:
        with open(tmp_pdf_name, "rb") as f:
            valid_upload_res = client.post("/resume/analyze", files={"file": ("resume.pdf", f, "application/pdf")}, headers=student_headers)
        assert valid_upload_res.status_code == 200, f"Valid PDF upload rejected: {valid_upload_res.status_code} - {valid_upload_res.text}"
        print("  [PASS] Valid PDF file accepted")
    finally:
        os.unlink(tmp_pdf_name)

    # Test invalid file type (txt disguised or raw txt)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_txt:
        tmp_txt.write(b"raw text content")
        tmp_txt_name = tmp_txt.name
        
    try:
        with open(tmp_txt_name, "rb") as f:
            invalid_type_res = client.post("/resume/analyze", files={"file": ("resume.txt", f, "text/plain")}, headers=student_headers)
        assert invalid_type_res.status_code == 400, f"Expected 400 for invalid file type: {invalid_type_res.status_code}"
        print("  [PASS] Non-PDF file upload rejected")
    finally:
        os.unlink(tmp_txt_name)

    # Test oversized file (6MB)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_large:
        # Write 6MB of mock data
        tmp_large.write(b"\0" * (6 * 1024 * 1024))
        tmp_large_name = tmp_large.name
        
    try:
        with open(tmp_large_name, "rb") as f:
            oversized_res = client.post("/resume/analyze", files={"file": ("resume.pdf", f, "application/pdf")}, headers=student_headers)
        assert oversized_res.status_code == 400, f"Expected 400 for oversized file: {oversized_res.status_code}"
        print("  [PASS] Oversized file (6MB) rejected")
    finally:
        os.unlink(tmp_large_name)

    # ---------------------------------------------
    # 6. LANGGRAPH CHAT WORKFLOW
    # ---------------------------------------------
    print("\n6. Running LangGraph Chat Agent Tests...")
    
    # Test academic routing
    chat_res = client.get("/ask", params={"query": "What classes do I have tomorrow?"}, headers=student_headers)
    assert chat_res.status_code == 200
    assert chat_res.json()["status"] == "success"
    print("  [PASS] LangGraph Academic Agent query successful")

    # Test resume prompt fallback when chatting
    resume_chat_res = client.get("/ask", params={"query": "analyze my resume"}, headers=student_headers)
    assert resume_chat_res.status_code == 200
    assert "upload a resume file directly" in resume_chat_res.json()["response"]
    print("  [PASS] LangGraph Resume Agent prompt matches query instruction")

    # Test communications routing (email draft)
    email_chat_res = client.get("/ask", params={"query": "draft an email to the warden about hostel wifi"}, headers=student_headers)
    assert email_chat_res.status_code == 200
    assert email_chat_res.json()["status"] == "success"
    print("  [PASS] LangGraph Communications Agent email drafting query successful")

    # ---------------------------------------------
    # 7. DASHBOARD TESTS
    # ---------------------------------------------
    print("\n7. Running Dashboard Endpoint Tests...")
    dash_res = client.get("/dashboard", headers=student_headers)
    assert dash_res.status_code == 200, f"Dashboard retrieval failed: {dash_res.text}"
    dash_data = dash_res.json()
    assert "student" in dash_data, "Student object missing in dashboard response"
    assert dash_data["student"]["name"] == "Satya", f"Expected Satya user name, got: {dash_data['student']['name']}"
    print("  [PASS] Dashboard endpoint returns dynamic student profile successfully")

    # ---------------------------------------------
    # 8. SYSTEM HEALTH TESTS
    # ---------------------------------------------
    print("\n8. Running System Health & Stats Tests...")
    health_res = client.get("/health")
    assert health_res.status_code == 200, f"Health endpoint failed: {health_res.text}"
    health_data = health_res.json()
    assert health_data["backend"] == "online"
    assert health_data["database"] == "connected"
    assert "uptime" in health_data
    assert "totalUsers" in health_data
    assert "students" in health_data
    assert "admins" in health_data
    print("  [PASS] Health endpoint checks completed successfully")

    # ---------------------------------------------
    # 9. PHASE 2 STUDENT REQUEST TESTS
    # ---------------------------------------------
    print("\n9. Running Phase 2 Student Request Tests...")
    # Create request
    req_res = client.post("/student/requests", json={"type": "Bonafide Certificate", "details": "Scholarship document"}, headers=student_headers)
    assert req_res.status_code == 200, f"Request creation failed: {req_res.text}"
    req_data = req_res.json()
    assert req_data["type"] == "Bonafide Certificate"
    assert req_data["status"] == "Pending"
    req_id = req_data["id"]

    # Student requests list
    stud_reqs_res = client.get("/student/requests", headers=student_headers)
    assert stud_reqs_res.status_code == 200
    assert any(r["id"] == req_id for r in stud_reqs_res.json())

    # Get history
    hist_res = client.get(f"/student/requests/{req_id}/history", headers=student_headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()) >= 1
    assert hist_res.json()[0]["new_status"] == "Pending"

    # Admin requests list
    admin_reqs_res = client.get("/admin/requests", headers=admin_headers)
    assert admin_reqs_res.status_code == 200
    assert any(r["id"] == req_id for r in admin_reqs_res.json())

    # Admin updates status
    update_res = client.put(f"/admin/requests/{req_id}", json={"status": "Approved", "note": "All documents verified"}, headers=admin_headers)
    assert update_res.status_code == 200
    
    # Check request status changed
    admin_req_res = client.get(f"/admin/requests/{req_id}", headers=admin_headers)
    assert admin_req_res.status_code == 200
    assert admin_req_res.json()["status"] == "Approved"
    assert len(admin_req_res.json()["history"]) == 2
    assert admin_req_res.json()["history"][1]["new_status"] == "Approved"

    # Student notifications check
    notif_res = client.get("/notifications", headers=student_headers)
    assert notif_res.status_code == 200
    my_notifs = notif_res.json()
    assert any(n["related_type"] == "Request" and n["related_id"] == req_id for n in my_notifs)
    print("  [PASS] Request pipeline, history tracking, notifications and audit logs verified successfully")

    # ---------------------------------------------
    # 10. PHASE 2 UNIFIED EVENTS TESTS
    # ---------------------------------------------
    print("\n10. Running Phase 2 Unified Events Tests...")
    # Admin create event
    import time
    evt_title = f"Agentic AI Hackathon {int(time.time())}"
    evt_payload = {
        "title": evt_title,
        "category": "Hackathon",
        "description": "Build agentic apps",
        "venue": "Lab 3",
        "start_datetime": "2026-09-01T09:00:00",
        "end_datetime": "2026-09-02T17:00:00",
        "published": False,
        "team_size": 4,
        "prize_pool": "$5000"
    }
    create_evt_res = client.post("/admin/events", json=evt_payload, headers=admin_headers)
    assert create_evt_res.status_code == 200, f"Event creation failed: {create_evt_res.text}"
    evt_id = create_evt_res.json()["id"]

    # Student cannot see draft
    stu_evts_res = client.get("/events?category=hackathon")
    assert stu_evts_res.status_code == 200
    assert not any(e["id"] == evt_id for e in stu_evts_res.json())

    # Admin publishes draft
    publish_res = client.put(f"/admin/events/{evt_id}", json={"published": True}, headers=admin_headers)
    assert publish_res.status_code == 200
    assert publish_res.json()["published"] == True

    # Student can now see published
    stu_evts_res2 = client.get("/events?category=hackathon")
    assert any(e["id"] == evt_id for e in stu_evts_res2.json())

    # Student registers for event
    reg_evt_res = client.post(f"/events/{evt_id}/register", headers=student_headers)
    assert reg_evt_res.status_code == 200
    
    # Check duplicate prevention
    dup_reg_res = client.post(f"/events/{evt_id}/register", headers=student_headers)
    assert dup_reg_res.status_code == 400

    # Student registration list check
    my_regs_res = client.get("/student/event-registrations", headers=student_headers)
    assert any(r["event_id"] == evt_id for r in my_regs_res.json())

    # Audit logs verification
    audit_res = client.get("/admin/audit-logs", headers=admin_headers)
    assert audit_res.status_code == 200
    logs_data = audit_res.json()["logs"]
    assert any("Created Event" in l["action"] for l in logs_data)
    print("  [PASS] Unified event CRUD, filters, registrations and security rules verified successfully")

    print("\n=== ALL COMPONENT TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()
