# CampusOS Architecture Specification — Baseline (Pre-Refactoring)

## Overview
CampusOS is an AI-powered student assistant and administrative coordinator application with a React-based frontend and FastAPI-based backend.

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
                                    | SQLite DB     |     | JSON Files    |
                                    | (campus.db)   |     | (data/*.json) |
                                    +---------------+     +---------------+
```

## Functional Components

### 1. Frontend SPA Routing
*   **Routing Logic:** Defined in [`App.jsx`](file:///e:/Agentx/frontend/src/App.jsx).
*   **Security Guards:** Uses `<ProtectedRoute>` inside [`ProtectedRoute.jsx`](file:///e:/Agentx/frontend/src/components/ProtectedRoute.jsx) which checks for `access_token` in `localStorage`.
*   **Role Separation:** Missing from the client. All pages (including Communications which contains admin form fields) are accessible to both students and admins.

### 2. Backend Gateway & API Controllers
*   **Server Setup:** Defined in [`main.py`](file:///e:/Agentx/backend/main.py) using FastAPI.
*   **Routing:** Defined in [`routes.py`](file:///e:/Agentx/backend/api/routes.py).
*   **Auth Verification:** Token extraction and payload parsing is done via `get_current_user` in `routes.py`, querying the `User` model.
*   **Role Enforcement (RBAC)**: Enforced via `require_admin` dependency for announcements and push notifications. However, `GET /admin/clusters` lacks this guard, creating a vulnerability.

### 3. Agent Coordination (LangGraph)
*   **Graph Setup:** StateGraph with a single supervisor node in [`graph.py`](file:///e:/Agentx/backend/graph.py).
*   **Execution Node:** Defined in [`nodes.py`](file:///e:/Agentx/backend/nodes.py). Contains handler branches for Academic, Placement, Knowledge, Notification, Events, and Student Services agents.
*   **Broken Agent Loops:** Routes to `ResumeAgent` and `CommunicationAgent` are ignored in `nodes.py` due to missing execution blocks.

### 4. Storage Setup
*   **Relational Database:** SQLite (`campus.db`) mapped via SQLAlchemy in `backend/database/`.
*   **Vector DB:** Chroma vector store in `backend/vector_db/` loaded with FastEmbed embeddings.
*   **Local File Stores:** Flat JSON files inside `backend/data/` for event registrations, grievances, appointments, reminders, and announcements.

### Key Functional Discrepancies
*   **Disconnected Data Paths**: Grievance tickets are written to `grievances.json`, but the admin complaint clustering algorithm queries from the SQLite `complaints` table (which is always empty).
*   **Resolution Sync Break**: Admin resolution broadcasts write resolutions to the SQLite `announcements` table. However, the student communications feed reads exclusively from `announcements.json`.
*   **Hardcoded Identity**: Student ID is hardcoded to `"S001"` for all event registrations and cancellations.
