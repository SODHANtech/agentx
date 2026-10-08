def test_admin_login(client):
    response = client.post("/auth/login", json={"email": "admin@campus.edu", "password": "admin123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Admin"
    assert "access_token" in response.cookies


def test_student_login(client):
    response = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "student123"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "Student"
    assert data["user"]["cgpa"] == 8.5


def test_invalid_login(client):
    response = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "wrong_password"})
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


def test_get_current_user_profile(client, student_headers):
    response = client.get("/auth/me", headers=student_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "satya@campus.edu"
    assert data["role"] == "Student"


def test_student_registration(client):
    payload = {
        "name": "Arun Kumar",
        "email": "arun@campus.edu",
        "password": "securepass123",
        "role": "Student",
        "cgpa": 7.8,
        "backlogs": 1
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["email"] == "arun@campus.edu"
    assert data["message"] == "User registered successfully"

    # Now verify login with the newly registered user
    login_res = client.post("/auth/login", json={"email": "arun@campus.edu", "password": "securepass123"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_cookie_authenticated_request(client):
    # Perform login to obtain cookie
    login_res = client.post("/auth/login", json={"email": "satya@campus.edu", "password": "student123"})
    assert login_res.status_code == 200
    cookies = login_res.cookies

    # Send request without Authorization header, using cookie only
    me_res = client.get("/auth/me", cookies=cookies)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "satya@campus.edu"
