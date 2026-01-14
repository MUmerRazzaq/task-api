"""Contract tests for GET /tasks endpoint."""



class TestListTasksEndpoint:
    """Contract tests for listing tasks."""

    async def test_list_tasks_empty(self, client):
        """GET /tasks should return empty array when no tasks exist."""
        response = await client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert data == []

    async def test_list_tasks_returns_all(self, client, sample_task_data):
        """GET /tasks should return all created tasks."""
        # Create multiple tasks
        await client.post("/tasks", json={"title": "Task 1"})
        await client.post("/tasks", json={"title": "Task 2"})
        await client.post("/tasks", json={"title": "Task 3"})

        response = await client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    async def test_list_tasks_includes_all_fields(self, client, sample_task_data):
        """GET /tasks should include all task fields."""
        await client.post("/tasks", json=sample_task_data)

        response = await client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        task = data[0]
        assert "id" in task
        assert "title" in task
        assert "description" in task
        assert "is_completed" in task
        assert "created_at" in task
        assert "updated_at" in task

    async def test_list_tasks_ordered_newest_first(self, client):
        """GET /tasks should return tasks ordered by created_at DESC."""
        import asyncio

        await client.post("/tasks", json={"title": "First task"})
        await asyncio.sleep(0.01)
        await client.post("/tasks", json={"title": "Second task"})
        await asyncio.sleep(0.01)
        await client.post("/tasks", json={"title": "Third task"})

        response = await client.get("/tasks")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Newest first
        assert data[0]["title"] == "Third task"
        assert data[1]["title"] == "Second task"
        assert data[2]["title"] == "First task"
