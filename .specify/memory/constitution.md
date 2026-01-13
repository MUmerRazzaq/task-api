<!--
Sync Impact Report:
- Version change: Initial (no prior version) → 1.0.0
- Modified principles: N/A (initial constitution)
- Added sections:
  * I. Test-Driven Development (TDD)
  * II. Specification-First Development
  * III. Simplicity Over Cleverness
  * IV. Single Responsibility
  * Technology Stack
  * API Design Standards
  * Testing Requirements
- Removed sections: N/A (initial constitution)
- Templates requiring updates:
  ✅ plan-template.md (reviewed - Constitution Check section aligns)
  ✅ spec-template.md (reviewed - requirements structure aligns)
  ✅ tasks-template.md (reviewed - TDD test-first approach aligns)
- Follow-up TODOs: None
-->

# Task Management API Constitution

## Core Principles

### I. Test-Driven Development (TDD)

Tests MUST be written before implementation. No feature is considered complete without tests. All testing is performed using pytest.

**Rationale**: TDD ensures code correctness, improves design quality, provides living documentation, and prevents regressions. Writing tests first forces clarity about expected behavior before implementation begins.

**Non-negotiable rules**:
- Write tests first → Tests fail → Implement → Tests pass (Red-Green-Refactor cycle)
- Every endpoint MUST have contract tests
- Every service layer MUST have unit tests
- Every user journey MUST have integration tests
- No code is merged without accompanying tests
- Test coverage is a quality gate, not a metric to game

### II. Specification-First Development

API behavior MUST be clearly defined before coding begins. Endpoints, schemas, request/response formats, and error codes are explicit and documented.

**Rationale**: Specification-first development enables parallel work (frontend/backend), reduces integration issues, provides clear contracts, and improves API consistency. Clear specs prevent ambiguity and wasted effort.

**Non-negotiable rules**:
- API endpoints are documented before implementation
- Request/response schemas are defined using Pydantic models
- Error responses follow consistent format
- Breaking changes require version increments
- OpenAPI/Swagger documentation is auto-generated and accurate

### III. Simplicity Over Cleverness

Prefer readable, maintainable code over clever solutions. Optimize for human understanding, not lines-of-code minimization.

**Rationale**: Code is read far more often than written. Simple code is easier to understand, debug, extend, and onboard new developers to. Cleverness creates knowledge silos and maintenance burden.

**Non-negotiable rules**:
- Avoid unnecessary abstractions
- No premature optimization
- Explicit is better than implicit
- Code should be self-documenting where possible
- Comments explain "why", not "what"
- Complexity must be justified (see plan-template.md Complexity Tracking)

### IV. Single Responsibility

Each module, function, and class MUST have one clear responsibility. Separation of concerns is enforced at all levels.

**Rationale**: Single responsibility makes code easier to test, change, and reason about. It reduces coupling, improves reusability, and makes the system more modular.

**Non-negotiable rules**:
- Models contain only data and validation logic
- Services contain business logic
- Routers/controllers handle HTTP concerns only
- Database access is isolated in repository pattern or service layer
- Dependencies flow in one direction (no circular imports)
- Each function does one thing well

## Technology Stack

The project MUST use the following technologies:

- **FastAPI** (latest stable) — REST API framework
- **SQLModel** (latest stable) — ORM and database models combining SQLAlchemy + Pydantic
- **PostgreSQL via Neon DB** — Production and development database
- **pytest** (latest stable) — Testing framework
- **Pydantic** (v2+) — Data validation and schema definition
- **Alembic** (via SQLModel) — Database migrations

**Constraints**:
- Python 3.11+ required
- Async/await patterns preferred for I/O operations
- Type hints required on all function signatures
- No third-party abstractions that hide framework capabilities

## API Design Standards

All API endpoints MUST follow these standards:

### Endpoint Structure
- RESTful resource-based URLs (`/tasks`, `/tasks/{id}`)
- Proper HTTP methods (GET, POST, PUT, PATCH, DELETE)
- Consistent response formats (success and error)
- HTTP status codes used correctly (200, 201, 400, 404, 500, etc.)

### Request/Response Format
- All requests validated using Pydantic models
- All responses use defined schemas (no raw dicts)
- Timestamps in ISO 8601 format
- IDs are UUIDs (not auto-incrementing integers)
- Pagination for list endpoints (limit/offset or cursor-based)

### Error Handling
- Consistent error response structure:
  ```json
  {
    "detail": "Error message",
    "error_code": "RESOURCE_NOT_FOUND",
    "field_errors": {} // optional for validation errors
  }
  ```
- Meaningful error messages
- Appropriate HTTP status codes
- No stack traces exposed in production

## Testing Requirements

### Test Organization
- `tests/contract/` — API contract tests (endpoint inputs/outputs)
- `tests/integration/` — Multi-component integration tests
- `tests/unit/` — Isolated unit tests for business logic

### Test Coverage
- All endpoints MUST have contract tests
- All service methods MUST have unit tests
- Critical user journeys MUST have integration tests
- Edge cases and error paths MUST be tested
- Database operations MUST be tested with real database (testcontainers or test DB)

### Test Quality
- Tests are independent (no shared state)
- Tests use descriptive names (test_create_task_with_valid_data_returns_201)
- Fixtures used for common setup
- Mocking used judiciously (prefer real components when practical)
- Tests run fast (< 5 seconds for unit tests, < 30 seconds for integration suite)

## Development Workflow

### Pre-Implementation
1. Write or review feature specification (spec.md)
2. Create implementation plan (plan.md)
3. Generate task breakdown (tasks.md)
4. Identify architectural decisions requiring ADRs

### Implementation Cycle
1. Write failing tests (Red)
2. Implement minimum code to pass (Green)
3. Refactor for quality (Refactor)
4. Commit with descriptive message
5. Repeat

### Code Review Requirements
- All code requires review before merge
- Tests pass in CI/CD
- No linting/formatting violations
- Constitution compliance verified
- No unresolved TODOs or FIXMEs

## Governance

This constitution supersedes all other practices and conventions. All development work, code reviews, and architectural decisions MUST comply with these principles.

### Amendment Process
- Amendments require documented justification
- Breaking changes require team discussion
- Version increments follow semantic versioning:
  - **MAJOR**: Backward-incompatible principle removals or redefinitions
  - **MINOR**: New principles added or material guidance expansion
  - **PATCH**: Clarifications, wording fixes, non-semantic refinements

### Compliance
- All pull requests MUST verify compliance during review
- Any deviation from principles requires justification in plan.md Complexity Tracking table
- Use `.specify/memory/constitution.md` (this file) as authoritative source
- Runtime development guidance follows patterns in CLAUDE.md

### Quality Gates
- Tests pass (no exceptions)
- Type checks pass (mypy or similar)
- Linting passes (ruff or similar)
- Code coverage meets minimum threshold (80%+)
- Security scans pass (no high/critical vulnerabilities)

**Version**: 1.0.0 | **Ratified**: 2026-01-12 | **Last Amended**: 2026-01-12
