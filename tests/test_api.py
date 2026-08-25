def test_submit_task(client):

    payload = {
        "name": "test_job",
        "payload":{"key":"value"}
    }

    response  = client.post("/api/v1/tasks/", json=payload)

    assert response.status_code == 202

    data = response.json()
    assert "id" in data
    assert data["name"] == "test_job"
    assert data["status"] == "PENDING"
    assert data["payload"] == {"key": "value"}