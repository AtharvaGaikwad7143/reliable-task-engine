from unittest.mock import patch


@patch("src.api.tasks.process_task.delay")
def test_submit_task(mock_process_task, client):

    payload = {
        "name": "test_job",
        "payload": {
            "key": "value"
        }
    }

    response = client.post(
        "/api/v1/tasks/",
        json=payload
    )

    assert response.status_code == 202

    data = response.json()

    assert "id" in data
    assert data["name"] == "test_job"
    assert data["status"] == "PENDING"
    assert data["payload"] == {"key": "value"}

    # Celery task trigger hua?
    mock_process_task.assert_called_once()

    # Celery ko same task ID diya?
    called_with_uuid = mock_process_task.call_args[0][0]

    assert called_with_uuid == data["id"]