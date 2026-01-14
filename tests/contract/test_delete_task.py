"""Contract tests for DELETE /tasks/{task_id} endpoint."""

from uuid import uuid4


class TestDeleteTaskEndpoint:
    """Contract tests for task deletion."""

    async def test_delete_existing_task(self, client, sample_task_data):
        """DELETE /tasks/{id} should return 204 for existing task."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        response = await client.delete(f"/tasks/{task_id}")

        assert response.status_code == 204
        assert response.content == b""

    async def test_delete_task_removes_from_database(self, client, sample_task_data):
        """DELETE /tasks/{id} should remove task from database."""
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Delete the task
        delete_response = await client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        # Verify task is gone
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_task_returns_404(self, client):
        """DELETE /tasks/{id} for non-existent task should return 404."""
        fake_id = str(uuid4())

        response = await client.delete(f"/tasks/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "TASK_NOT_FOUND"

    async def test_delete_only_affects_target_task(self, client):
        """DELETE /tasks/{id} should only remove the specified task."""
        # Create multiple tasks
        task1_response = await client.post("/tasks", json={"title": "Task 1"})
        task2_response = await client.post("/tasks", json={"title": "Task 2"})
        task3_response = await client.post("/tasks", json={"title": "Task 3"})

        task1_id = task1_response.json()["id"]
        task2_id = task2_response.json()["id"]
        task3_id = task3_response.json()["id"]

        # Delete task 2
        await client.delete(f"/tasks/{task2_id}")

        # Verify task 1 and 3 still exist
        assert (await client.get(f"/tasks/{task1_id}")).status_code == 200
        assert (await client.get(f"/tasks/{task3_id}")).status_code == 200

        # Verify task 2 is gone
        assert (await client.get(f"/tasks/{task2_id}")).status_code == 404

        # Verify list only has 2 tasks
        list_response = await client.get("/tasks")
        assert len(list_response.json()) == 2

    async def test_delete_completed_task(self, client, sample_task_data):
        """DELETE /tasks/{id} should work for completed tasks."""
        # Create and complete a task
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]
        await client.put(f"/tasks/{task_id}", json={"is_completed": True})

        # Delete the completed task
        response = await client.delete(f"/tasks/{task_id}")

        assert response.status_code == 204
