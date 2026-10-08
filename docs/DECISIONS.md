# CampusOS Architecture & Design Decisions

This document records the architectural design decisions made during the hardening of the CampusOS application.

## 1. Modular Monolith vs Microservices
* **Decision**: Refactor the backend into a modular-monolith directory layout (`backend/app/core/` and `backend/app/modules/`).
* **Rationale**: Microservices would introduce latency, deployment overhead, and networking complexity. A modular monolith enforces clean boundaries while keeping deployments simple, sharing a single relational database.

## 2. Authentication Cookie-based Storage
* **Decision**: Transition the frontend from `localStorage` token storage to secure `HttpOnly`, `Secure`, `SameSite=Strict` cookies.
* **Rationale**: Eliminates XSS (Cross-Site Scripting) exposure to user authentication tokens.

## 3. Database Abstraction and Connection Configuration
* **Decision**: Keep SQLAlchemy and integrate Alembic for migrations, setting up the `DATABASE_URL` config variable to route between SQLite (Dev) and PostgreSQL (Prod).
* **Rationale**: Alembic allows schema version logs. Database independence enables development in a local single-file SQLite database and deployment to standard production SQL database clusters.

## 4. Controlled AI Gateway Pattern
* **Decision**: Restructure Chatbot logic to route prompts through an AI Gateway that resolves intents to backend service methods, rather than letting the LLM execute arbitrary database reads/writes.
* **Rationale**: The LLM must not bypass system security rules, authorization scopes, and resource ownership checks. Treating user queries as untrusted inputs preserves code safety.

## 5. Conversational Request Intent Handlers
* **Decision**: Limit the LangGraph router's conversational request creation to specific, structured parameters.
* **Rationale**: Keeps chatbot interactions clean and ensures all records submitted conversationally generate notifications and request histories matching regular portal forms.
