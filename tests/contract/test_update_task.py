"""Contract tests for PUT /tasks/{task_id} endpoint."""

from uuid import uuid4


class TestUpdateTaskEndpoint:
    """Contract tests for task updates."""

    async def test_update_task_full(self, client, sample_task_data):
        """PUT /tasks/{id} should update all fields."""
        # Create task first
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Update all fields
        update_data = {
            "title": "Updated title",
            "description": "Updated description",
            "is_completed": True,
        }
        response = await client.put(f"/tasks/{task_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Updated title"
        assert data["description"] == "Updated description"
        assert data["is_completed"] is True

    async def test_update_task_partial_title(self, client, sample_task_data):
        """PUT /tasks/{id} should support partial update (title only)."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        original_description = create_response.json()["description"]

        response = await client.put(
            f"/tasks/{task_id}",
            json={"title": "New title only"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New title only"
        assert data["description"] == original_description
        assert data["is_completed"] is False

    async def test_update_task_partial_is_completed(self, client, sample_task_data):
        """PUT /tasks/{id} should support partial update (is_completed only)."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        original_title = create_response.json()["title"]

        response = await client.put(
            f"/tasks/{task_id}",
            json={"is_completed": True},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == original_title
        assert data["is_completed"] is True

    async def test_update_task_updates_timestamp(self, client, sample_task_data):
        """PUT /tasks/{id} should update the updated_at timestamp."""
        import asyncio

        create_response = await client.post("/tasks", json=sample_task_data)
        task = create_response.json()
        original_updated_at = task["updated_at"]

        await asyncio.sleep(0.01)

        response = await client.put(
            f"/tasks/{task['id']}",
            json={"title": "Updated"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["updated_at"] != original_updated_at
        assert data["created_at"] == task["created_at"]

    async def test_update_task_empty_title_returns_400(self, client, sample_task_data):
        """PUT /tasks/{id} with empty title should return 400."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        response = await client.put(f"/tasks/{task_id}", json={"title": ""})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_update_task_whitespace_title_returns_400(self, client, sample_task_data):
        """PUT /tasks/{id} with whitespace-only title should return 400."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        response = await client.put(f"/tasks/{task_id}", json={"title": "   "})

        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"

    async def test_update_nonexistent_task_returns_404(self, client):
        """PUT /tasks/{id} for non-existent task should return 404."""
        fake_id = str(uuid4())

        response = await client.put(
            f"/tasks/{fake_id}",
            json={"title": "Update"},
        )

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "TASK_NOT_FOUND"

    async def test_update_task_can_clear_description(self, client, sample_task_data):
        """PUT /tasks/{id} should allow clearing description to null."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        assert create_response.json()["description"] is not None

        response = await client.put(
            f"/tasks/{task_id}",
            json={"description": None},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] is None

    async def test_update_task_can_toggle_completion(self, client, sample_task_data):
        """PUT /tasks/{id} should allow toggling completion status."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Mark as complete
        response1 = await client.put(
            f"/tasks/{task_id}",
            json={"is_completed": True},
        )
        assert response1.status_code == 200
        assert response1.json()["is_completed"] is True

        # Mark as incomplete
        response2 = await client.put(
            f"/tasks/{task_id}",
            json={"is_completed": False},
        )
        assert response2.status_code == 200
        assert response2.json()["is_completed"] is False
