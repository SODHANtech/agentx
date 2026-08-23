# CampusOS Architecture Specification — Final Target State

## Overview
CampusOS is an AI-powered student assistant and administrative coordinator application with a React-based frontend and FastAPI-based backend. Following the architectural refactoring, SQLite acts as the single source of truth for all mutable application state.

```
+------------------+           HTTP           +-----------------+
|  React Frontend  | <----------------------> | FastAPI Backend |
|   (Vite, SPA)    |                          |    (Uvicorn)    |
+------------------+                          +--------+--------+
                                                       |
                                            +----------+----------+
                                            |                     |
                                            v                     v
                                    +---------------+     +---------------+
                                    | SQLite DB     |     | Static JSONs  |
                                    | (campus.db)   |     | (data/*.json) |
                                    +---------------+     +---------------+
```

## Functional Components

### 1. Frontend SPA Routing & Role Guards
*   **Routing Logic:** Defined in [`App.jsx`](file:///e:/Agentx/frontend/src/App.jsx).
*   **Security Guards:** `<ProtectedRoute>` in [`ProtectedRoute.jsx`](file:///e:/Agentx/frontend/src/components/ProtectedRoute.jsx) parses JWT tokens from `localStorage` to enforce role verification.
*   **Role Separation:** The `Sidebar.jsx` and `Communications.jsx` tabs dynamically adjust options based on the user's role:
    *   **Admin**: Access to "Complaint Radar" (semantic clustering and broadcast) and administrative notification/announcement forms.
    *   **Student**: Forbidden from accessing `/admin-radar` routes and administrative dashboard capabilities.
*   **Error Interceptor:** Axios automatically clears tokens and redirects to `/login` if any backend API request returns a `401 Unauthorized` status.

### 2. Backend Gateway & API Controllers
*   **Server Setup:** FastAPI gateway running via Uvicorn in [`main.py`](file:///e:/Agentx/backend/main.py).
*   **Routing:** Defined in [`routes.py`](file:///e:/Agentx/backend/api/routes.py).
*   **Auth Verification:** Handled using `get_current_user` to match database profiles. Self-registration forces the `Student` role on new accounts.
*   **Role-Based Access Control (RBAC):** Administrative endpoints (such as `/admin/clusters` and `/admin/clusters/{cluster_id}/broadcast`) are guarded by the `require_admin` dependency.

### 3. Agent Coordination (LangGraph)
*   **Graph Setup:** StateGraph orchestrator in [`graph.py`](file:///e:/Agentx/backend/graph.py).
*   **Execution Nodes:** Defined in [`nodes.py`](file:///e:/Agentx/backend/nodes.py). Contains handler branches for all active agents.
*   **Completed Agent Loops:**
    *   `ResumeAgent`: Returns a controlled prompt instruction if no resume is uploaded.
    *   `CommunicationAgent`: Extracts email parameters or appointment slots via LLM helper prompts, performing actions directly in SQLite.
*   **Deterministic Routing:** Keywords are isolated and analyzed directly from the current user question in `router.py`, preventing historical conversation context from corrupting regex router matches.

### 4. Storage & Persistence Setup
*   **Relational Database:** SQLite (`campus.db`) mapped via SQLAlchemy models in `backend/database/models.py`. Actively tracks:
    *   `User`: Student and Administrator profiles.
    *   `Complaint` & `ComplaintCluster`: Student grievances and semantic clusters.
    *   `EventRegistration`: User registrations for campus events.
    *   `Appointment` & `Notification`: Scheduled slots and notifications.
    *   `Announcement`: Systemic resolutions and announcements.
*   **Vector DB:** Chroma vector store in `backend/vector_db/` for handbook text retrieval.
*   **Static Asset Stores:** Flat JSON files inside `backend/data/` for immutable data only (`timetable.json`, `events.json`, `companies.json`, `student_services.json`). All mutable JSON files have been deleted.

### 5. Security & Verification
*   **Secret Keys:** The application validates that default insecure JWT secrets are not allowed in production environments in `backend/config.py`.
*   **Upload Boundaries:** Resume uploads enforce a strict 5MB size limit and require `application/pdf` MIME type and file extension matching.
*   **Automated Verification:** Verified by `backend/scripts/test_rest_endpoints.py` covering Auth, RBAC, Event isolation, Grievance flow, and file upload validations.
