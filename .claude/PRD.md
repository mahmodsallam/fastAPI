Atlas — Product Requirements Document
Version: 0.1 (Draft for review)
Status: Proposed; implementation requires approval
Product: Atlas — Enterprise Knowledge & Workflow Platform
Primary audience: Small engineering teams and project administrators
Initial interface: REST API with OpenAPI/Swagger; minimal web UI later
1. Product overview
Atlas is a multi-user platform for organizing projects, assigning and tracking tasks, storing project documents, and eventually answering questions grounded in those documents. The initial product is a conventional, secure backend. AI functionality is deliberately deferred until the backend is complete and tested.
2. Problem and opportunity
Engineering teams scatter project information across task lists, documents, and individual contributors. Atlas provides a coherent API-first workspace for managing project work and knowledge. Later, a permission-aware AI assistant will make this information searchable and actionable.
3. Goals
1. Deliver a documented, deployed FastAPI backend demonstrating practical backend engineering.
2. Support project/task workflows with persistence, authentication, and authorization.
3. Build a reliable foundation for document ingestion and future retrieval-augmented generation (RAG).
4. Demonstrate engineering skills relevant to AI Engineering and Forward Deployed Engineering: API design, data modeling, integrations, security, observability, and evaluation.
Non-goals for initial backend
- LLM integration, embeddings, agents, or vector search.
- Mobile app or polished frontend.
- Billing, enterprise SSO, multi-tenant organizations, real-time collaboration, or complex workflow automation.
- Microservices; begin with a modular monolith.
4. Users and roles
- Visitor: Can register or log in; cannot access project data.
- Member: Can view accessible projects and create/update permitted tasks.
- Project admin: Can manage membership and project settings.
- Project owner: Has final authority over project membership and deletion.
Authorization rule: Project data must not be accessible to non-members. The precise member/admin permissions will be approved before implementation of the authorization milestone.
5. Core user journeys
1. Register, log in, and receive an access token.
2. Create a project and become its owner.
3. Add members to a project and assign roles.
4. Create, view, edit, filter, and complete tasks within accessible projects.
5. Upload and retrieve documents associated with a project.
6. Later: ask a question about accessible project documents and receive an answer with citations.
6. Functional requirements
FR-01 Projects — P0, Milestone 1
- Create project with name and optional description.
- List projects and retrieve a project by ID.
- Update project name/description.
- Delete a project.
- Validate input; return appropriate HTTP statuses and consistent errors.
- For Milestone 1, use an in-memory repository and a single-user assumption only as a temporary learning scaffold. Replace it with persistence and authorization in later milestones.
FR-02 Tasks — P0, Milestones 1–2
- Create tasks within a project with title, optional description, and status.
- List, retrieve, update, and delete tasks.
- Supported statuses initially: todo, in_progress, done.
- Reject tasks for nonexistent projects; use stable identifiers.
- Add database relationships, pagination, filtering, and sorting in subsequent milestones.
FR-03 Persistence — P0, Milestone 2
- Persist projects, tasks, users, and memberships in PostgreSQL.
- Use SQLAlchemy 2.x and Alembic migrations.
- Enforce referential integrity and explicit deletion behavior.
- Provide reproducible local setup with Docker Compose.
FR-04 Identity and access — P0, Milestone 3
- Register/login with secure password hashing.
- Authenticate protected endpoints using bearer JWTs.
- Enforce project-level membership and owner/admin permissions.
- Ensure a user cannot retrieve or mutate unauthorized project data.
- Avoid logging secrets or tokens; store credentials in environment variables.
FR-05 Documents — P1, Milestone 4
- Upload documents to an authorized project, with metadata in PostgreSQL.
- List, download, and delete documents subject to permissions.
- Validate allowed file types and maximum sizes; use safe storage keys.
- Local storage is acceptable for development; deployment storage is selected later.
FR-06 Reliability and API quality — P0, Milestones 1–5
- Generate accurate OpenAPI documentation.
- Validate requests/responses with Pydantic v2.
- Use predictable HTTP statuses and a consistent error envelope.
- Test happy paths, validation errors, missing resources, and authorization boundaries.
- Add structured logs, health endpoints, pagination, and CI.
FR-07 AI knowledge assistant — P2, Milestone 6+ only
- Extract text from supported project documents.
- Chunk and embed content, storing vectors with project/document ownership metadata.
- Retrieve only documents the requesting user is authorized to access.
- Answer document-grounded questions with traceable source citations.
- Evaluate retrieval relevance, answer grounding, latency, and failure cases against a small labeled dataset.
- Do not claim accuracy without measurement; handle insufficient evidence explicitly.
7. Initial data model (proposed)
- User: id, email (unique), password_hash, created_at.
- Project: id, name, description, owner_id, created_at, updated_at.
- ProjectMembership: user_id, project_id, role, created_at; unique (user_id, project_id).
- Task: id, project_id, title, description, status, assignee_id (nullable), created_at, updated_at.
- Document: id, project_id, filename, content_type, size_bytes, storage_key, uploaded_by, created_at.
Identifiers: UUIDs proposed. Timestamps: UTC. Final field constraints, cascade policies, and permission matrix require approval before implementation.
8. Milestone 1 API contract (proposed)
All endpoints are under /api/v1. No authentication or database in this milestone.
Method	Endpoint	Purpose	Success
POST	/projects	Create project	201
GET	/projects	List projects	200
GET	/projects/{project_id}	Get project	200
PUT	/projects/{project_id}	Replace editable project fields	200
DELETE	/projects/{project_id}	Delete project	204
POST	/projects/{project_id}/tasks	Create task	201
GET	/projects/{project_id}/tasks	List tasks	200
GET	/projects/{project_id}/tasks/{task_id}	Get task	200
PUT	/projects/{project_id}/tasks/{task_id}	Replace editable task fields	200
DELETE	/projects/{project_id}/tasks/{task_id}	Delete task	204


Suggested error behavior: 404 unknown resource, 422 invalid request, 409 for genuine state conflicts. 401 and 403 apply after authentication and authorization are added. PUT is full replacement of editable fields; consider PATCH later for partial updates.
Initial schemas (proposed)
- ProjectCreate: name (required, 1–120 chars), description (optional, max 2000 chars).
- ProjectRead: id, name, description, created_at, updated_at.
- ProjectUpdate: same editable fields as create.
- TaskCreate: title (required, 1–200 chars), description (optional), status (default todo).
- TaskRead: id, project_id, title, description, status, created_at, updated_at.
- TaskUpdate: same editable fields as create.
9. Non-functional requirements
- Maintainability: Modular monolith; thin routers, services for business logic, repository abstraction only when justified.
- Security: No hard-coded secrets; input validation; least-privilege authorization; file upload constraints.
- Quality: Automated tests in CI; target at least 80% coverage of core business logic by the end of backend milestones (coverage is a signal, not proof of correctness).
- Performance: For local demo-sized data, target p95 under 300 ms for ordinary CRUD requests excluding file transfers; measure rather than assume.
- Observability: Structured logs, request IDs, health/readiness endpoints; never log passwords or tokens.
- Reproducibility: README, .env.example, lockfile, migrations, Docker Compose, repeatable test commands.
10. Delivery roadmap and exit criteria
M1 — FastAPI API foundation
Projects and tasks CRUD; Pydantic schemas; OpenAPI; in-memory repository; pytest endpoint tests. Exit: all routes work, documented statuses, tests pass, design is understood and reviewed.
M2 — Database
PostgreSQL, SQLAlchemy, migrations, relationships, persistence tests. Exit: data survives restart; migrations apply to a fresh DB; referential integrity verified.
M3 — Security
Registration/login, JWT, role-based access, project membership. Exit: unauthorized and cross-project access tests pass.
M4 — Production capabilities
Document management, pagination/filtering, logging, expanded testing. Exit: uploads are validated; task list can be paginated; failure paths are tested.
M5 — Deployment and UI
Docker, CI, hosted deployment, minimal dashboard. Exit: clean deployment from repository, smoke tests and documented setup.
M6 — AI extension
Text ingestion, vector search, permission-aware RAG, source citations, evaluation. Exit: demonstrated answers grounded in authorized documents and evaluation results documented.
11. Definition of done (each feature)
- Requirements and API contract approved before code.
- Implementation is small, understandable, and type-checked/linted where configured.
- Tests cover happy path and relevant failure/edge cases.
- OpenAPI and README updated when behavior changes.
- No secrets committed; no unresolved critical security issue.
- Developer can explain design decisions without AI assistance.
12. Risks and open decisions
1. Confirm UUID vs integer IDs.
2. Confirm PUT only vs PATCH for partial updates.
3. Approve permission matrix for member/admin/owner.
4. Decide deletion semantics (cascade vs soft delete).
5. Select deployment platform and document storage backend later.
6. Decide whether a web UI is needed before the AI milestone.
7. Confirm which FastAPI course sections require additional hands-on exercises beyond the mapped topics.
13. Success metrics
- M1: all ten CRUD routes tested, OpenAPI accurate, validation and 404 behavior verified.
- M3: cross-project access denial demonstrated by automated tests.
- M5: running hosted demo and reproducible local environment.
- M6: documented RAG evaluation dataset, measured grounding/retrieval performance, and cited answers.