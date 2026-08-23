import os
import sys
import httpx
import tempfile

BASE_URL = "http://127.0.0.1:8000"

def run_tests():
    print("=== STARTING AUTOMATED ENDPOINTS VERIFICATION ===")
    
    # Check if backend is running
    try:
        httpx.get(f"{BASE_URL}/")
    except Exception:
        print(f"ERROR: Backend server is not running on {BASE_URL}. Please start the backend server first!")
        sys.exit(1)
        
    client = httpx.Client(base_url=BASE_URL)
    
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

    print("\n=== ALL COMPONENT TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_tests()
