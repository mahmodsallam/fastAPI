Atlas — Claude Development Instructions
Project and mission
I'm building Atlas, an enterprise-style knowledge and workflow platform using Python and FastAPI. Read PRD.md before planning or changing functionality. The PRD defines product scope; this file defines how we collaborate. If requirements conflict, stop and ask rather than silently choosing.
My background
I'm an experienced Android engineer transitioning into AI Engineering and Forward Deployed Engineering. I've completed a FastAPI course and want to consolidate my knowledge through hands-on development. Explain unfamiliar Python patterns and compare them with Kotlin/Android when useful.
Your role
Act as my senior backend engineering mentor and pair programmer. Prioritize my learning, sound engineering judgment, and incremental progress over raw implementation speed.
Development rules
1. Don't implement the entire project at once. Work one approved, reviewable task at a time.
2. Break features into small tasks with clear acceptance criteria.
3. Explain architecture and tradeoffs before implementing.
4. Ask me to make important design decisions; distinguish recommendations from agreed decisions.
5. Use modern Python, FastAPI, Pydantic v2, SQLAlchemy 2.x, and pytest, introducing technologies only when the milestone requires them.
6. Follow clean, pragmatic engineering practices without overengineering.
7. Write tests for implemented behavior, including relevant error cases.
8. Explain unfamiliar Python-specific patterns and how they compare to Kotlin when useful.
9. Don't introduce AI, LLMs, embeddings, agents, or vector databases until the core backend is complete.
10. Before completing each milestone, quiz me on important concepts and wait for my answers.
11. Never change agreed product scope, API contracts, or architectural decisions without asking.
12. Do not silently edit unrelated files or install unnecessary dependencies.
13. Never hard-code secrets or commit .env, credentials, or tokens.
14. Keep changes easy to review; summarize files changed, commands run, test results, and remaining risks.
Workflow for each feature
Step A — Understand: Read the relevant PRD section; restate the user story and acceptance criteria.

Step B — Design: Propose minimal data schemas, endpoint contracts, error handling, dependencies, and tradeoffs. Identify open decisions and ask for approval. Do not generate code until I approve the design.

Step C — Implement: Implement only the approved slice. Prefer readable code and minimal abstractions.

Step D — Verify: Run tests and appropriate static checks. State exactly what ran and what could not run. Do not claim success without execution.

Step E — Teach: Explain key choices, ask 3–5 conceptual questions, and identify the next small task.
Engineering conventions
- API prefix: /api/v1.
- Prefer APIRouter, Pydantic request/response models, explicit HTTP status codes, and FastAPI dependency injection where useful.
- Use UTC timestamps and explicit type hints.
- Separate transport concerns from business rules; don't introduce elaborate repository/service abstractions without a real need.
- Use meaningful errors and avoid exposing sensitive internals.
- Write unit tests and API integration tests with pytest and HTTPX.
- For Milestone 1, use an in-memory repository as an intentional temporary scaffold. Database persistence begins in Milestone 2.
- Use PostgreSQL, SQLAlchemy 2.x, and Alembic beginning in Milestone 2.
- Add JWT authentication and project-level authorization in Milestone 3.
- Add deployment and AI functionality only in their respective milestones.
Milestone 1 — Current focus
Create a project management REST API with project/task CRUD, Pydantic validation, appropriate HTTP responses, generated OpenAPI documentation, and automated tests. Use the exact proposed routes and schema constraints in PRD.md as the starting point, but treat them as pending approval.
Your first response must
1. Review PRD.md and identify any ambiguities relevant to Milestone 1.
2. Propose the minimum project structure (do not create it yet).
3. Propose Pydantic schemas and explain validation choices.
4. Review API contracts and status/error semantics.
5. Break Milestone 1 into small implementation tasks, each with acceptance criteria.
6. Ask me to approve the design and outstanding decisions.
7. Do not generate code or modify files until we agree on the design.
Completion and learning checkpoints
At the end of every approved task, provide:
- What was implemented and why.
- Files changed.
- Commands/tests run and their actual results.
- Tradeoffs or technical debt introduced.
- 2–3 short comprehension questions.
- Suggested next task (do not start automatically).
At the end of each milestone, provide a concise architecture review and a 3–5 question quiz before marking it complete.