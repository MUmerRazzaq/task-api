"""Contract tests for GET /tasks/{task_id} endpoint."""

from uuid import uuid4


class TestGetTaskEndpoint:
    """Contract tests for retrieving a single task."""

    async def test_get_existing_task(self, client, sample_task_data):
        """GET /tasks/{id} should return the task."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        response = await client.get(f"/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]

    async def test_get_task_includes_all_fields(self, client, sample_task_data):
        """GET /tasks/{id} should include all task fields."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        response = await client.get(f"/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "title" in data
        assert "description" in data
        assert "is_completed" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_get_nonexistent_task_returns_404(self, client):
        """GET /tasks/{id} for non-existent task should return 404."""
        fake_id = str(uuid4())

        response = await client.get(f"/tasks/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "TASK_NOT_FOUND"
        assert "detail" in data

    async def test_get_task_invalid_uuid_returns_400(self, client):
        """GET /tasks/{id} with invalid UUID should return 400."""
        response = await client.get("/tasks/not-a-uuid")

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
