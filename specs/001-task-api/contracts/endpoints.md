# API Endpoints: Task Management API

**Feature**: 001-task-api
**Date**: 2026-01-13
**Version**: 1.0.0

## Base URL

```
http://localhost:8000
```

## Endpoints Overview

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/tasks` | List all tasks | None |
| POST | `/tasks` | Create a new task | None |
| GET | `/tasks/{task_id}` | Get a specific task | None |
| PUT | `/tasks/{task_id}` | Update a task | None |
| DELETE | `/tasks/{task_id}` | Delete a task | None |

---

## 1. List All Tasks

### Request

```http
GET /tasks HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Response (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Write documentation",
    "description": "Create API docs for task endpoints",
    "is_completed": false,
    "created_at": "2026-01-13T10:30:00Z",
    "updated_at": "2026-01-13T10:30:00Z"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "title": "Deploy to production",
    "description": null,
    "is_completed": true,
    "created_at": "2026-01-13T09:15:00Z",
    "updated_at": "2026-01-13T11:45:00Z"
  }
]
```

### Response Codes

- `200 OK`: Successful response (empty array if no tasks)
- `500 Internal Server Error`: Server error

### Notes

- Tasks ordered by creation date (newest first)
- Empty array returned if no tasks exist
- No pagination in MVP (all tasks returned)

---

## 2. Create Task

### Request

```http
POST /tasks HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/json

{
  "title": "Write documentation",
  "description": "Create API docs for task endpoints"
}
```

### Request Body

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | Yes | 1-200 chars, non-whitespace | Brief task description |
| `description` | string \| null | No | None | Detailed task information |

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Write documentation",
  "description": "Create API docs for task endpoints",
  "is_completed": false,
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

### Response (400 Bad Request)

```json
{
  "detail": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "field_errors": {
    "title": [
      "Title cannot be empty or whitespace only"
    ]
  }
}
```

### Response Codes

- `201 Created`: Task created successfully
- `400 Bad Request`: Invalid request data (validation error)
- `500 Internal Server Error`: Server error

### Validation Rules

1. **Title**:
   - MUST NOT be empty string
   - MUST NOT be whitespace-only
   - MUST be 1-200 characters (after trimming)
   - Leading/trailing whitespace automatically trimmed

2. **Description**:
   - Optional (can be omitted or null)
   - No length constraints

### Example cURL

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Write documentation",
    "description": "Create API docs for task endpoints"
  }'
```

---

## 3. Get Task by ID

### Request

```http
GET /tasks/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
Accept: application/json
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Unique task identifier |

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Write documentation",
  "description": "Create API docs for task endpoints",
  "is_completed": false,
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T10:30:00Z"
}
```

### Response (404 Not Found)

```json
{
  "detail": "Task with id 550e8400-e29b-41d4-a716-446655440000 not found",
  "error_code": "TASK_NOT_FOUND"
}
```

### Response Codes

- `200 OK`: Task found and returned
- `404 Not Found`: Task does not exist
- `500 Internal Server Error`: Server error

### Example cURL

```bash
curl http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

---

## 4. Update Task

### Request

```http
PUT /tasks/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
Content-Type: application/json
Accept: application/json

{
  "title": "Finalize documentation",
  "description": "Add examples and review",
  "is_completed": true
}
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Unique task identifier |

### Request Body

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `title` | string | No | 1-200 chars, non-whitespace | Updated task title |
| `description` | string \| null | No | None | Updated description |
| `is_completed` | boolean | No | true/false | Updated completion status |

**Note**: At least one field should be provided, but all fields are technically optional. Providing no fields results in a no-op update (only `updated_at` changes).

### Response (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Finalize documentation",
  "description": "Add examples and review",
  "is_completed": true,
  "created_at": "2026-01-13T10:30:00Z",
  "updated_at": "2026-01-13T12:00:00Z"
}
```

### Response (400 Bad Request)

```json
{
  "detail": "Validation error",
  "error_code": "VALIDATION_ERROR",
  "field_errors": {
    "title": [
      "Title cannot be empty or whitespace only"
    ]
  }
}
```

### Response (404 Not Found)

```json
{
  "detail": "Task with id 550e8400-e29b-41d4-a716-446655440000 not found",
  "error_code": "TASK_NOT_FOUND"
}
```

### Response Codes

- `200 OK`: Task updated successfully
- `400 Bad Request`: Invalid request data (validation error)
- `404 Not Found`: Task does not exist
- `500 Internal Server Error`: Server error

### Partial Updates

PUT endpoint supports partial updates:

```json
// Update only completion status
{
  "is_completed": true
}

// Update only title
{
  "title": "New title"
}

// Clear description (set to null)
{
  "description": null
}
```

### Example cURL

```bash
curl -X PUT http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000 \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Finalize documentation",
    "is_completed": true
  }'
```

---

## 5. Delete Task

### Request

```http
DELETE /tasks/550e8400-e29b-41d4-a716-446655440000 HTTP/1.1
Host: localhost:8000
```

### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task_id` | UUID | Unique task identifier |

### Response (204 No Content)

```
(Empty response body)
```

### Response (404 Not Found)

```json
{
  "detail": "Task with id 550e8400-e29b-41d4-a716-446655440000 not found",
  "error_code": "TASK_NOT_FOUND"
}
```

### Response Codes

- `204 No Content`: Task deleted successfully
- `404 Not Found`: Task does not exist
- `500 Internal Server Error`: Server error

### Notes

- Deletion is permanent (no soft delete)
- No undo mechanism in MVP
- Returns 204 even if task was already deleted (idempotent operation debatable - currently returns 404 for consistency)

### Example cURL

```bash
curl -X DELETE http://localhost:8000/tasks/550e8400-e29b-41d4-a716-446655440000
```

---

## Common Response Fields

### Success Response (Task object)

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique task identifier |
| `title` | string | Task title |
| `description` | string \| null | Task description (can be null) |
| `is_completed` | boolean | Completion status |
| `created_at` | datetime | Creation timestamp (ISO 8601) |
| `updated_at` | datetime | Last update timestamp (ISO 8601) |

### Error Response

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error message |
| `error_code` | string | Machine-readable error code |
| `field_errors` | object | Field-specific validation errors (optional) |

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request data |
| `TASK_NOT_FOUND` | 404 | Task does not exist |
| `INTERNAL_SERVER_ERROR` | 500 | Server error |

---

## HTTP Headers

### Request Headers

```
Content-Type: application/json    (for POST/PUT requests)
Accept: application/json           (recommended for all requests)
```

### Response Headers

```
Content-Type: application/json
```

---

## Timestamp Format

All timestamps use **ISO 8601 format** with UTC timezone:

```
2026-01-13T10:30:00Z
```

Format: `YYYY-MM-DDTHH:MM:SSZ`

---

## Testing Examples

### Happy Path Flow

```bash
# 1. Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Test task", "description": "Testing the API"}'

# Response: 201 Created with task object (note the id)

# 2. List all tasks
curl http://localhost:8000/tasks

# Response: 200 OK with array containing the created task

# 3. Get specific task
curl http://localhost:8000/tasks/{id-from-step-1}

# Response: 200 OK with task details

# 4. Update task
curl -X PUT http://localhost:8000/tasks/{id-from-step-1} \
  -H "Content-Type: application/json" \
  -d '{"is_completed": true}'

# Response: 200 OK with updated task (updated_at changed)

# 5. Delete task
curl -X DELETE http://localhost:8000/tasks/{id-from-step-1}

# Response: 204 No Content

# 6. Try to get deleted task
curl http://localhost:8000/tasks/{id-from-step-1}

# Response: 404 Not Found
```

### Error Cases

```bash
# Empty title validation
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": ""}'
# Response: 400 Bad Request with VALIDATION_ERROR

# Non-existent task
curl http://localhost:8000/tasks/00000000-0000-0000-0000-000000000000
# Response: 404 Not Found with TASK_NOT_FOUND

# Invalid UUID format
curl http://localhost:8000/tasks/invalid-uuid
# Response: 400 Bad Request (FastAPI automatic validation)
```

---

## Implementation Mapping

| Endpoint | User Story | Functional Requirements |
|----------|------------|------------------------|
| POST /tasks | US1 - Create | FR-001, FR-002, FR-003, FR-004, FR-010, FR-014 |
| GET /tasks | US1 - View all | FR-005, FR-012 |
| GET /tasks/{id} | US1 - View one | FR-006, FR-013 |
| PUT /tasks/{id} | US2 - Update | FR-007, FR-008, FR-010, FR-013 |
| DELETE /tasks/{id} | US3 - Delete | FR-009, FR-013 |

---

## Future Considerations (Out of Scope)

Potential enhancements not in MVP:
- Pagination for GET /tasks (limit/offset or cursor-based)
- Filtering (e.g., `?is_completed=true`)
- Sorting (e.g., `?sort=created_at&order=desc`)
- Bulk operations (create/update/delete multiple tasks)
- PATCH for partial updates (currently using PUT with optional fields)
- Search by title/description
- Task history/audit log

---

## Summary

**Endpoint Count**: 5
**Authentication**: None (single-user MVP)
**Data Format**: JSON
**Response Time**: <200ms p95 for all operations
**Concurrency**: Supports 100+ concurrent users
**Error Handling**: Consistent format with error codes
**Validation**: Automatic via Pydantic + custom validators
