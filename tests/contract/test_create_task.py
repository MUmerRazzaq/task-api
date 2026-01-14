"""Contract tests for POST /tasks endpoint."""



class TestCreateTaskEndpoint:
    """Contract tests for task creation."""

    async def test_create_task_with_valid_data(self, client, sample_task_data):
        """POST /tasks should return 201 with created task."""
        response = await client.post("/tasks", json=sample_task_data)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data["title"]
        assert data["description"] == sample_task_data["description"]
        assert data["is_completed"] is False
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_task_with_title_only(self, client, sample_task_data_minimal):
        """POST /tasks should accept title-only payload."""
        response = await client.post("/tasks", json=sample_task_data_minimal)

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_task_data_minimal["title"]
        assert data["description"] is None

    async def test_create_task_empty_title_returns_400(self, client):
        """POST /tasks with empty title should return 400."""
        response = await client.post("/tasks", json={"title": ""})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "field_errors" in data

    async def test_create_task_whitespace_title_returns_400(self, client):
        """POST /tasks with whitespace-only title should return 400."""
        response = await client.post("/tasks", json={"title": "   "})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_create_task_title_too_long_returns_400(self, client):
        """POST /tasks with title over 200 chars should return 400."""
        long_title = "a" * 201
        response = await client.post("/tasks", json={"title": long_title})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_create_task_missing_title_returns_400(self, client):
        """POST /tasks without title should return 400."""
        response = await client.post("/tasks", json={})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_create_task_returns_uuid_id(self, client, sample_task_data):
        """POST /tasks should return task with valid UUID id."""
        from uuid import UUID

        response = await client.post("/tasks", json=sample_task_data)

        assert response.status_code == 201
        data = response.json()
        # Should not raise
        UUID(data["id"])

    async def test_create_task_returns_iso_timestamps(self, client, sample_task_data):
        """POST /tasks should return ISO 8601 formatted timestamps."""
        from datetime import datetime

        response = await client.post("/tasks", json=sample_task_data)

        assert response.status_code == 201
        data = response.json()
        # Should not raise
        datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00"))
