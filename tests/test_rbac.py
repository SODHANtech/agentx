def test_unauthenticated_request_rejected(client):
    response = client.get("/admin/requests")
    assert response.status_code == 401
    assert "Missing or invalid authentication token" in response.json()["detail"]


def test_student_forbidden_from_admin_endpoints(client, student_headers):
    # Student attempts to access admin requests
    res1 = client.get("/admin/requests", headers=student_headers)
    assert res1.status_code == 403
    assert "Administrator role required" in res1.json()["detail"]

    # Student attempts to access admin clusters
    res2 = client.get("/admin/clusters", headers=student_headers)
    assert res2.status_code == 403

    # Student attempts to trigger semantic clustering
    res3 = client.post("/admin/complaints/cluster", headers=student_headers)
    assert res3.status_code == 403

    # Student attempts to access audit logs
    res4 = client.get("/admin/audit-logs", headers=student_headers)
    assert res4.status_code == 403


def test_admin_allowed_on_admin_endpoints(client, admin_headers):
    # Admin accesses admin requests
    res1 = client.get("/admin/requests", headers=admin_headers)
    assert res1.status_code == 200
    assert isinstance(res1.json(), list)

    # Admin accesses admin clusters
    res2 = client.get("/admin/clusters", headers=admin_headers)
    assert res2.status_code == 200

    # Admin accesses audit logs
    res3 = client.get("/admin/audit-logs", headers=admin_headers)
    assert res3.status_code == 200
