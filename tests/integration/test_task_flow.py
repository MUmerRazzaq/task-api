"""Integration tests for complete task flows."""



class TestCreateAndViewTaskFlow:
    """Integration tests for User Story 1: Create and View Tasks."""

    async def test_complete_create_and_view_flow(self, client):
        """Test complete create task → list tasks → get task flow."""
        # 1. Create a task
        task_data = {
            "title": "Write documentation",
            "description": "Create API documentation for task endpoints",
        }
        create_response = await client.post("/tasks", json=task_data)
        assert create_response.status_code == 201
        created_task = create_response.json()
        task_id = created_task["id"]

        # 2. Verify task appears in list
        list_response = await client.get("/tasks")
        assert list_response.status_code == 200
        tasks = list_response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == task_id
        assert tasks[0]["title"] == task_data["title"]

        # 3. Get task by ID
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 200
        retrieved_task = get_response.json()
        assert retrieved_task["id"] == task_id
        assert retrieved_task["title"] == task_data["title"]
        assert retrieved_task["description"] == task_data["description"]
        assert retrieved_task["is_completed"] is False

    async def test_multiple_tasks_ordered_correctly(self, client):
        """Test that multiple tasks are returned in correct order."""
        import asyncio

        # Create tasks with delays
        await client.post("/tasks", json={"title": "First task"})
        await asyncio.sleep(0.01)
        await client.post("/tasks", json={"title": "Second task"})
        await asyncio.sleep(0.01)
        await client.post("/tasks", json={"title": "Third task"})

        # List should have newest first
        response = await client.get("/tasks")
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 3
        assert tasks[0]["title"] == "Third task"
        assert tasks[1]["title"] == "Second task"
        assert tasks[2]["title"] == "First task"

    async def test_task_creation_with_minimal_data(self, client):
        """Test creating task with only required fields."""
        response = await client.post("/tasks", json={"title": "Minimal task"})

        assert response.status_code == 201
        task = response.json()
        assert task["title"] == "Minimal task"
        assert task["description"] is None
        assert task["is_completed"] is False
        assert "created_at" in task
        assert "updated_at" in task

    async def test_get_nonexistent_task_returns_404(self, client):
        """Test that getting a non-existent task returns 404."""
        from uuid import uuid4

        fake_id = str(uuid4())
        response = await client.get(f"/tasks/{fake_id}")

        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == "TASK_NOT_FOUND"


class TestUpdateTaskFlow:
    """Integration tests for User Story 2: Update Task Status and Details."""

    async def test_complete_update_flow(self, client):
        """Test create → update title → update completion → verify timestamps."""
        import asyncio

        # Create task
        create_response = await client.post(
            "/tasks",
            json={"title": "Draft proposal", "description": "Initial draft"},
        )
        assert create_response.status_code == 201
        task = create_response.json()
        task_id = task["id"]
        original_updated_at = task["updated_at"]

        await asyncio.sleep(0.01)

        # Update title
        update1_response = await client.put(
            f"/tasks/{task_id}",
            json={"title": "Finalize proposal"},
        )
        assert update1_response.status_code == 200
        task = update1_response.json()
        assert task["title"] == "Finalize proposal"
        assert task["updated_at"] != original_updated_at

        await asyncio.sleep(0.01)
        second_updated_at = task["updated_at"]

        # Mark as complete
        update2_response = await client.put(
            f"/tasks/{task_id}",
            json={"is_completed": True},
        )
        assert update2_response.status_code == 200
        task = update2_response.json()
        assert task["is_completed"] is True
        assert task["updated_at"] != second_updated_at

        # Verify via GET
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 200
        final_task = get_response.json()
        assert final_task["title"] == "Finalize proposal"
        assert final_task["is_completed"] is True

    async def test_update_preserves_other_fields(self, client):
        """Test that partial updates don't affect other fields."""
        # Create with all fields
        create_response = await client.post(
            "/tasks",
            json={"title": "Complete task", "description": "Important details"},
        )
        task = create_response.json()
        task_id = task["id"]

        # Update only completion status
        await client.put(f"/tasks/{task_id}", json={"is_completed": True})

        # Verify other fields unchanged
        get_response = await client.get(f"/tasks/{task_id}")
        task = get_response.json()
        assert task["title"] == "Complete task"
        assert task["description"] == "Important details"
        assert task["is_completed"] is True


class TestDeleteTaskFlow:
    """Integration tests for User Story 3: Remove Completed Tasks."""

    async def test_complete_delete_flow(self, client):
        """Test create → delete → verify 404 on get."""
        # Create task
        create_response = await client.post(
            "/tasks",
            json={"title": "Task to delete"},
        )
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # Delete task
        delete_response = await client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        # Verify 404 on get
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 404
        assert get_response.json()["error_code"] == "TASK_NOT_FOUND"

        # Verify 404 on update
        update_response = await client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated"},
        )
        assert update_response.status_code == 404

    async def test_delete_leaves_other_tasks_unchanged(self, client):
        """Test that deleting one task doesn't affect others."""
        # Create multiple tasks
        await client.post("/tasks", json={"title": "Keep this"})
        task2 = (await client.post("/tasks", json={"title": "Delete this"})).json()
        await client.post("/tasks", json={"title": "Keep this too"})

        # Delete task 2
        await client.delete(f"/tasks/{task2['id']}")

        # Verify other tasks unchanged
        list_response = await client.get("/tasks")
        tasks = list_response.json()
        assert len(tasks) == 2
        titles = [t["title"] for t in tasks]
        assert "Keep this" in titles
        assert "Keep this too" in titles
        assert "Delete this" not in titles

    async def test_full_lifecycle(self, client):
        """Test complete task lifecycle: create → update → complete → delete."""
        # Create
        create_response = await client.post(
            "/tasks",
            json={"title": "Full lifecycle test", "description": "Testing"},
        )
        task = create_response.json()
        task_id = task["id"]
        assert task["is_completed"] is False

        # Update
        await client.put(f"/tasks/{task_id}", json={"title": "Updated title"})

        # Complete
        await client.put(f"/tasks/{task_id}", json={"is_completed": True})

        # Verify state before delete
        get_response = await client.get(f"/tasks/{task_id}")
        task = get_response.json()
        assert task["title"] == "Updated title"
        assert task["is_completed"] is True

        # Delete
        delete_response = await client.delete(f"/tasks/{task_id}")
        assert delete_response.status_code == 204

        # Verify gone
        final_get = await client.get(f"/tasks/{task_id}")
        assert final_get.status_code == 404
