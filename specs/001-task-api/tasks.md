# Tasks: Task Management API

**Feature**: 001-task-api
**Input**: Design documents from `/specs/001-task-api/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/endpoints.md

**TDD Approach**: All tests must be written FIRST and FAIL before implementation (Red-Green-Refactor cycle)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Initialize Python 3.11+ project with uv package manager
- [X] T002 Create project structure with src/ and tests/ directories per plan.md
- [X] T003 [P] Add production dependencies (fastapi, uvicorn, sqlmodel, asyncpg, psycopg, pydantic, pydantic-settings, python-dotenv)
- [X] T004 [P] Add development dependencies (pytest, pytest-asyncio, httpx, ruff, mypy)
- [X] T005 [P] Configure pyproject.toml with test settings and tool configurations
- [X] T006 [P] Create .env.example with DATABASE_URL and LOG_LEVEL placeholders
- [X] T007 [P] Create .gitignore for Python, virtual environments, and secrets

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T008 Create database connection and async engine configuration in src/database.py
- [X] T009 Implement session management with FastAPI dependency injection in src/database.py
- [X] T010 Create database initialization function with SQLModel.metadata.create_all in src/database.py
- [X] T011 [P] Create pytest configuration in tests/conftest.py with test database fixtures
- [X] T012 [P] Implement test database engine fixture in tests/conftest.py
- [X] T013 [P] Implement test session fixture with transaction rollback in tests/conftest.py
- [X] T014 [P] Implement test client fixture with dependency overrides in tests/conftest.py
- [X] T015 Create FastAPI application instance in src/main.py with startup/shutdown events
- [X] T016 [P] Configure error handlers for consistent error response format in src/main.py
- [X] T017 [P] Create base Pydantic settings class in src/config.py for environment variables

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create and View Tasks (Priority: P1) 🎯 MVP

**Goal**: Enable users to create tasks and view them (core value proposition)

**Independent Test**: Create a task via API and retrieve it back. Delivers immediate value by allowing users to persist and recall their tasks.

**Acceptance Scenarios**:
1. Given no existing tasks, when user creates task with title "Write documentation", then system returns confirmation with unique identifier
2. Given user has created multiple tasks, when user requests all tasks, then system returns list with title, status, and creation date
3. Given a specific task exists, when user requests that task by identifier, then system returns complete task details

### Tests for User Story 1 (RED Phase - Write FIRST, ensure FAIL)

**⚠️ CRITICAL**: Write these tests FIRST, run them, and verify they FAIL before implementation

- [X] T018 [P] [US1] Write contract test for POST /tasks endpoint in tests/contract/test_create_task.py (test with valid data, empty title, whitespace title)
- [X] T019 [P] [US1] Write contract test for GET /tasks endpoint in tests/contract/test_list_tasks.py (test empty list, multiple tasks, ordering)
- [X] T020 [P] [US1] Write contract test for GET /tasks/{id} endpoint in tests/contract/test_get_task.py (test existing task, non-existent task)
- [X] T021 [P] [US1] Write unit test for Task model validation in tests/unit/test_task_model.py (test field constraints, defaults, UUID generation)
- [X] T022 [P] [US1] Write unit test for TaskCreate schema validation in tests/unit/test_task_schemas.py (test title validation, whitespace trimming)
- [X] T023 [P] [US1] Write unit test for TaskService.create_task in tests/unit/test_task_service.py (test task creation with valid/invalid data)
- [X] T024 [P] [US1] Write unit test for TaskService.get_task in tests/unit/test_task_service.py (test retrieval by ID, non-existent ID)
- [X] T025 [P] [US1] Write unit test for TaskService.list_tasks in tests/unit/test_task_service.py (test empty list, ordering by created_at DESC)
- [X] T026 [US1] Run all User Story 1 tests and verify they FAIL with ImportError or NotImplementedError

### Implementation for User Story 1 (GREEN Phase - Make tests PASS)

- [X] T027 [P] [US1] Create Task SQLModel entity in src/models/task.py with UUID, title, description, is_completed, created_at, updated_at fields
- [X] T028 [P] [US1] Create TaskCreate Pydantic schema in src/schemas/task.py with title validation (non-empty, non-whitespace, 1-200 chars)
- [X] T029 [P] [US1] Create TaskResponse Pydantic schema in src/schemas/task.py with all Task fields for API responses
- [X] T030 [US1] Run unit tests for models and schemas, verify T021-T022 pass
- [X] T031 [US1] Implement TaskService.create_task method in src/services/task_service.py (accepts TaskCreate, returns Task)
- [X] T032 [P] [US1] Implement TaskService.get_task method in src/services/task_service.py (retrieves by UUID, raises exception if not found)
- [X] T033 [P] [US1] Implement TaskService.list_tasks method in src/services/task_service.py (returns all tasks ordered by created_at DESC)
- [X] T034 [US1] Run unit tests for TaskService, verify T023-T025 pass
- [X] T035 [P] [US1] Implement POST /tasks endpoint in src/api/tasks.py (delegates to TaskService.create_task)
- [X] T036 [P] [US1] Implement GET /tasks endpoint in src/api/tasks.py (delegates to TaskService.list_tasks)
- [X] T037 [P] [US1] Implement GET /tasks/{task_id} endpoint in src/api/tasks.py (delegates to TaskService.get_task)
- [X] T038 [US1] Register tasks router in src/main.py
- [X] T039 [US1] Run contract tests for User Story 1 endpoints, verify T018-T020 pass
- [X] T040 [US1] Write integration test for complete create-and-view flow in tests/integration/test_task_flow.py
- [X] T041 [US1] Run integration test, verify it passes

### Refactor Phase for User Story 1

- [X] T042 [US1] Review and refactor User Story 1 code for clarity and maintainability (ensure tests still pass)
- [X] T043 [US1] Add error handling for TaskNotFoundError in src/api/tasks.py with 404 response
- [X] T044 [US1] Run all User Story 1 tests (contract, unit, integration) to verify complete functionality

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. MVP is ready for deployment!

---

## Phase 4: User Story 2 - Update Task Status and Details (Priority: P2)

**Goal**: Enable users to update task information as work progresses, including marking tasks as completed

**Independent Test**: Create a task, then update its title, description, or completion status. Delivers value by allowing users to keep their task list current.

**Acceptance Scenarios**:
1. Given an incomplete task exists, when user marks it as completed, then system updates status and last modified timestamp
2. Given task with title "Draft proposal", when user updates title to "Finalize proposal", then system updates title and timestamp
3. Given task without description, when user adds description, then system saves it and updates timestamp

### Tests for User Story 2 (RED Phase - Write FIRST, ensure FAIL)

- [X] T045 [P] [US2] Write contract test for PUT /tasks/{id} endpoint in tests/contract/test_update_task.py (test full update, partial update, invalid title, non-existent task)
- [X] T046 [P] [US2] Write unit test for TaskUpdate schema in tests/unit/test_task_schemas.py (test optional fields, validation rules)
- [X] T047 [P] [US2] Write unit test for TaskService.update_task in tests/unit/test_task_service.py (test various update scenarios, non-existent task)
- [X] T048 [US2] Run User Story 2 tests and verify they FAIL

### Implementation for User Story 2 (GREEN Phase - Make tests PASS)

- [X] T049 [US2] Create TaskUpdate Pydantic schema in src/schemas/task.py with optional title, description, is_completed fields
- [X] T050 [US2] Run unit test for TaskUpdate schema, verify T046 passes
- [X] T051 [US2] Implement TaskService.update_task method in src/services/task_service.py (retrieves task, applies updates, saves, returns updated task)
- [X] T052 [US2] Ensure updated_at timestamp is updated on any modification in TaskService.update_task
- [X] T053 [US2] Run unit test for TaskService.update_task, verify T047 passes
- [X] T054 [US2] Implement PUT /tasks/{task_id} endpoint in src/api/tasks.py (delegates to TaskService.update_task)
- [X] T055 [US2] Run contract test for PUT endpoint, verify T045 passes
- [X] T056 [US2] Write integration test for complete update flow in tests/integration/test_task_flow.py (create → update title → update completion → verify timestamps)
- [X] T057 [US2] Run integration test, verify it passes

### Refactor Phase for User Story 2

- [X] T058 [US2] Review and refactor User Story 2 code (ensure tests still pass)
- [X] T059 [US2] Run all User Story 2 tests (contract, unit, integration) to verify complete functionality

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Remove Completed Tasks (Priority: P3)

**Goal**: Enable users to delete tasks that are no longer relevant to keep their task list focused

**Independent Test**: Create tasks and delete them. Delivers value by helping users maintain a clean, focused task list.

**Acceptance Scenarios**:
1. Given a completed task exists, when user deletes it, then system removes it permanently and confirms deletion
2. Given a task was deleted, when user attempts to view or update that task, then system responds with clear message
3. Given multiple tasks exist, when user deletes one task, then system removes only that task and other tasks remain unchanged

### Tests for User Story 3 (RED Phase - Write FIRST, ensure FAIL)

- [X] T060 [P] [US3] Write contract test for DELETE /tasks/{id} endpoint in tests/contract/test_delete_task.py (test successful deletion, non-existent task, verify 204 response)
- [X] T061 [P] [US3] Write unit test for TaskService.delete_task in tests/unit/test_task_service.py (test deletion, non-existent task)
- [X] T062 [US3] Run User Story 3 tests and verify they FAIL

### Implementation for User Story 3 (GREEN Phase - Make tests PASS)

- [X] T063 [US3] Implement TaskService.delete_task method in src/services/task_service.py (retrieves task, deletes it, raises exception if not found)
- [X] T064 [US3] Run unit test for TaskService.delete_task, verify T061 passes
- [X] T065 [US3] Implement DELETE /tasks/{task_id} endpoint in src/api/tasks.py (delegates to TaskService.delete_task, returns 204 No Content)
- [X] T066 [US3] Run contract test for DELETE endpoint, verify T060 passes
- [X] T067 [US3] Write integration test for complete delete flow in tests/integration/test_task_flow.py (create → delete → verify 404 on get)
- [X] T068 [US3] Run integration test, verify it passes

### Refactor Phase for User Story 3

- [X] T069 [US3] Review and refactor User Story 3 code (ensure tests still pass)
- [X] T070 [US3] Run all User Story 3 tests (contract, unit, integration) to verify complete functionality

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [X] T071 [P] Add type hints to all functions and validate with mypy
- [X] T072 [P] Run ruff linter and fix any code style issues across all files
- [X] T073 [P] Review all error messages for clarity and consistency with FR-011
- [X] T074 Run complete test suite (all contract, integration, unit tests) and verify 100% pass
- [X] T075 [P] Verify test coverage is >80% with pytest --cov=src (90% achieved)
- [ ] T076 Manual testing via FastAPI /docs endpoint for all 5 endpoints
- [ ] T077 [P] Verify database persistence across server restarts (FR-012)
- [ ] T078 [P] Test concurrent operations with multiple simultaneous requests (SC-007: 100 concurrent users)
- [ ] T079 [P] Measure response times and verify <2s for create/retrieve (SC-001), <1s for list operations (SC-002)
- [ ] T080 Document any deviations from spec.md or plan.md in README.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion (can run in parallel with US1 if staffed, but requires US1 endpoints for integration testing)
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion (can run in parallel with US1/US2 if staffed)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational - Uses US1 endpoints in integration tests
- **User Story 3 (P3)**: Can start after Foundational - Uses US1 endpoints in integration tests

### Within Each User Story (TDD Flow)

1. **RED Phase**: Write all tests FIRST, run them, verify they FAIL
2. **GREEN Phase**: Implement minimum code to make tests pass
   - Models before services
   - Services before endpoints
   - Unit tests pass before contract tests
   - Contract tests pass before integration tests
3. **REFACTOR Phase**: Improve code quality while keeping tests green

### Parallel Opportunities

- **Phase 1 (Setup)**: Tasks T003-T007 can run in parallel
- **Phase 2 (Foundational)**: Tasks T011-T014, T016-T017 can run in parallel after T008-T010
- **User Story 1 Tests**: Tasks T018-T025 can run in parallel (all test writing)
- **User Story 1 Implementation**: Tasks T027-T029 can run in parallel (models/schemas), T032-T033 can run in parallel (service methods), T035-T037 can run in parallel (endpoints)
- **User Story 2 Tests**: Tasks T045-T047 can run in parallel
- **User Story 3 Tests**: Tasks T060-T061 can run in parallel
- **Polish**: Tasks T071-T073, T075, T077-T079 can run in parallel

---

## Parallel Example: User Story 1

### RED Phase (Write tests in parallel)
```bash
# Launch all test writing tasks for User Story 1 together:
Task T018: "Write contract test for POST /tasks endpoint"
Task T019: "Write contract test for GET /tasks endpoint"
Task T020: "Write contract test for GET /tasks/{id} endpoint"
Task T021: "Write unit test for Task model validation"
Task T022: "Write unit test for TaskCreate schema validation"
Task T023: "Write unit test for TaskService.create_task"
Task T024: "Write unit test for TaskService.get_task"
Task T025: "Write unit test for TaskService.list_tasks"
# Then: Run all tests → Verify they FAIL (T026)
```

### GREEN Phase (Implement in parallel where possible)
```bash
# Launch model/schema tasks together:
Task T027: "Create Task SQLModel entity"
Task T028: "Create TaskCreate Pydantic schema"
Task T029: "Create TaskResponse Pydantic schema"
# Then: Run unit tests T021-T022 (T030)

# Launch service methods together:
Task T032: "Implement TaskService.get_task"
Task T033: "Implement TaskService.list_tasks"
# Then: Run unit tests T023-T025 (T034)

# Launch endpoint tasks together:
Task T035: "Implement POST /tasks endpoint"
Task T036: "Implement GET /tasks endpoint"
Task T037: "Implement GET /tasks/{task_id} endpoint"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (TDD: RED → GREEN → REFACTOR)
4. **STOP and VALIDATE**: Test User Story 1 independently via /docs
5. Deploy/demo MVP (core create and view functionality working)

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP! 🎯)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (TDD cycle)
   - Developer B: User Story 2 (TDD cycle) - waits for US1 endpoints for integration tests
   - Developer C: User Story 3 (TDD cycle) - waits for US1 endpoints for integration tests
3. Stories complete and integrate independently

---

## TDD Workflow Summary

### For Each Task Group (RED-GREEN-REFACTOR)

1. **RED Phase**:
   - Write all tests for the user story
   - Run: `uv run pytest tests/unit/` (should FAIL)
   - Run: `uv run pytest tests/contract/` (should FAIL)
   - Verify failures are due to missing implementation (ImportError, NotImplementedError)

2. **GREEN Phase**:
   - Implement minimum code to pass tests
   - Start with models/schemas
   - Then services
   - Then endpoints
   - Run tests after each layer: `uv run pytest -v`
   - Verify tests turn green incrementally

3. **REFACTOR Phase**:
   - Improve code quality
   - Add type hints
   - Extract duplicated logic
   - Simplify complex functions
   - Run: `uv run pytest` (should still PASS)

---

## Summary

**Total Tasks**: 80
**MVP Tasks**: 44 (Phases 1-3: Setup + Foundational + User Story 1)
**User Story Breakdown**:
- Setup: 7 tasks
- Foundational: 10 tasks (BLOCKS all stories)
- User Story 1 (P1): 27 tasks (16 tests + 11 implementation)
- User Story 2 (P2): 15 tasks (4 tests + 11 implementation)
- User Story 3 (P3): 11 tasks (3 tests + 8 implementation)
- Polish: 10 tasks

**Parallel Opportunities**: 28 tasks marked [P] can run in parallel within their phases

**Independent Test Criteria**:
- US1: Create task via POST, retrieve via GET /tasks and GET /tasks/{id}
- US2: Create task, update title/description/status via PUT, verify changes
- US3: Create task, delete via DELETE, verify 404 on subsequent GET

**Suggested MVP Scope**: Phases 1-3 (User Story 1) = 44 tasks

**Tests**: TDD approach - all tests written FIRST (RED), then implementation (GREEN), then refactor

---

## Notes

- **[P]** tasks = different files, no dependencies within phase
- **[Story]** label maps task to specific user story for traceability
- Each user story follows TDD: Write failing tests → Implement → Refactor
- Verify tests fail before implementing (RED phase is critical!)
- Run `uv run pytest -v` frequently to verify test status
- Commit after each phase or logical checkpoint
- Stop at any checkpoint to validate story independently via `/docs`
- Avoid premature optimization - make tests pass first, refactor later
