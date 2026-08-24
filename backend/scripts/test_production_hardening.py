import httpx
import sys
import time

BASE_URL = "http://127.0.0.1:8000"

def run_hardening_tests():
    print("=== STARTING PRODUCTION HARDENING AUDIT TESTS ===")
    
    # 1. Check server connectivity
    try:
        httpx.get(f"{BASE_URL}/")
    except Exception:
        print(f"ERROR: Backend server is not running on {BASE_URL}. Please start it first!")
        sys.exit(1)
        
    client = httpx.Client(base_url=BASE_URL)

    # ==========================================
    # Test 1: Cookie-Based Authentication
    # ==========================================
    print("\n1. Testing Cookie-Based Authentication & Session...")
    
    # Login & get cookies
    login_res = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "student123"})
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    
    cookies = login_res.cookies
    assert "access_token" in cookies, "Cookie 'access_token' was not set upon login!"
    print("  [PASS] Login successfully set the access_token cookie")

    # Fetch profile using cookie (without Authorization header)
    cookie_client = httpx.Client(base_url=BASE_URL, cookies=cookies)
    me_res = cookie_client.get("/auth/me")
    assert me_res.status_code == 200, f"Failed to authenticate using cookies: {me_res.text}"
    assert me_res.json()["email"] == "satya@campus.edu"
    print("  [PASS] Successfully retrieved user profile using fallback session cookie")

    # Logout
    logout_res = cookie_client.post("/auth/logout")
    assert logout_res.status_code == 200, "Logout request failed!"
    print("  [PASS] Logout endpoint successfully called")

    # Verify cookie was cleared and access is now forbidden
    me_after_logout = cookie_client.get("/auth/me")
    assert me_after_logout.status_code == 401, f"Expected 401 Unauthorized after logout, got {me_after_logout.status_code}"
    print("  [PASS] Session invalidated; access properly rejected post-logout")

    # ==========================================
    # Test 2: Database Exception Mapping
    # ==========================================
    print("\n2. Testing Database Exception Protection...")
    db_err_res = client.get("/test/db-error")
    assert db_err_res.status_code == 500, f"Expected 500 Internal Server Error, got: {db_err_res.status_code}"
    
    response_json = db_err_res.json()
    assert "detail" in response_json, "Response does not contain details block"
    assert "database operation error occurred" in response_json["detail"], f"Exposed system information! Response detail: {response_json['detail']}"
    print("  [PASS] Internal database exceptions correctly caught and tracebacks protected")

    # ==========================================
    # Test 3: Event Conflict Validation on Updates
    # ==========================================
    print("\n3. Testing Event Title Conflict Validation...")
    # Log in as Admin
    admin_login = client.post("/auth/login", json={"email": "admin@campus.edu", "password": "admin123"})
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create two test events
    title_a = f"Event Alpha {int(time.time())}"
    title_b = f"Event Beta {int(time.time())}"
    
    evt_a_res = client.post("/admin/events", json={
        "title": title_a, "category": "Seminar", "description": "Desc A", "venue": "Hall A",
        "start_datetime": "2026-09-01T10:00:00", "end_datetime": "2026-09-01T12:00:00", "published": True
    }, headers=admin_headers)
    assert evt_a_res.status_code == 200
    id_a = evt_a_res.json()["id"]

    evt_b_res = client.post("/admin/events", json={
        "title": title_b, "category": "Seminar", "description": "Desc B", "venue": "Hall B",
        "start_datetime": "2026-09-01T10:00:00", "end_datetime": "2026-09-01T12:00:00", "published": True
    }, headers=admin_headers)
    assert evt_b_res.status_code == 200
    id_b = evt_b_res.json()["id"]

    # Try to update Event B's title to match Event A (conflict)
    conflict_res = client.put(f"/admin/events/{id_b}", json={"title": title_a}, headers=admin_headers)
    assert conflict_res.status_code == 400, f"Expected 400 Bad Request on duplicate title update, got: {conflict_res.status_code}"
    print("  [PASS] Conflict checks verified; duplicate title modifications rejected")

    # ==========================================
    # Test 4: Rate Limiting
    # ==========================================
    print("\n4. Testing API Rate Limiter...")
    # Trigger login rate limiting (login limit is 10/min)
    rate_limited = False
    for i in range(12):
        res = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "wrongpassword"})
        if res.status_code == 429:
            rate_limited = True
            break
            
    assert rate_limited, "Failed to trigger rate limiting on login endpoint!"
    print("  [PASS] Endpoint rate limiting verified (HTTP 429 returned on abuse)")

    print("\n=== ALL HARDENING AUDIT TESTS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_hardening_tests()
