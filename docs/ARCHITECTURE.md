# CampusOS Architecture Specification — Phase 2 Target State

## Overview
CampusOS is an AI-powered student assistant and administrative coordinator application featuring a React-based frontend SPA and a FastAPI-based backend. SQLite is the single source of truth for all mutable application state.

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

---

## 1. Relational Database Design
The SQLite database (`campus.db`) tracks all mutable state. Phase 2 unifies events, notifications, and logging into a single relational scheme.

### Schemas

#### User Table (`users`)
*   `id` (INTEGER, PK, Autoincrement)
*   `name` (VARCHAR, Not Null)
*   `email` (VARCHAR, Unique, Indexed, Not Null)
*   `password_hash` (VARCHAR, Not Null)
*   `role` (VARCHAR, Default 'Student') — `'Student' | 'Admin'`
*   `status` (VARCHAR, Default 'Active') — `'Active' | 'Suspended'`
*   `cgpa` (FLOAT, Default 0.0)
*   `backlogs` (INTEGER, Default 0)
*   `roll_number` (VARCHAR, Nullable) — Student Roll Number
*   `department` (VARCHAR, Nullable) — Sponsoring/Major Department
*   `created_at` (DATETIME, Default current_timestamp)

#### Requests Table (`requests`)
*   `id` (INTEGER, PK, Autoincrement)
*   `student_id` (INTEGER, FK -> `users.id`, Not Null)
*   `type` (VARCHAR, Not Null) — `'Bonafide' | 'Leave' | 'Doubt'`
*   `details` (TEXT, Not Null)
*   `status` (VARCHAR, Default 'Pending') — `'Pending' | 'Under Review' | 'Approved' | 'Rejected' | 'Completed'`
*   `created_at` (DATETIME, Default current_timestamp)

#### Request History Table (`request_histories`)
*   `id` (INTEGER, PK, Autoincrement)
*   `request_id` (INTEGER, FK -> `requests.id`, Not Null)
*   `previous_status` (VARCHAR, Nullable)
*   `new_status` (VARCHAR, Not Null)
*   `changed_by` (INTEGER, FK -> `users.id`, Not Null)
*   `note` (TEXT, Nullable)
*   `timestamp` (DATETIME, Default current_timestamp)

#### Unified Events Table (`events`)
*   `id` (INTEGER, PK, Autoincrement)
*   `title` (VARCHAR, Unique, Indexed, Not Null)
*   `category` (VARCHAR, Not Null) — `'Event' | 'Hackathon' | 'Seminar' | 'Workshop' | 'Competition' | 'Guest Lecture'`
*   `description` (TEXT, Not Null)
*   `venue` (VARCHAR, Not Null)
*   `start_datetime` (DATETIME, Not Null)
*   `end_datetime` (DATETIME, Not Null)
*   `registration_link` (VARCHAR, Nullable)
*   `max_participants` (INTEGER, Default 0)
*   `published` (BOOLEAN, Default False)
*   `created_by` (INTEGER, FK -> `users.id`, Not Null)
*   `created_at` (DATETIME, Default current_timestamp)
*   `organizer` (VARCHAR, Nullable) — Club/Association hosting the event
*   `department` (VARCHAR, Nullable) — Academic department hosting
*   `banner_poster` (VARCHAR, Nullable) — URL/Path to graphics asset
*   `eligibility` (VARCHAR, Nullable) — CGPA/Department constraints
*   `team_size` (INTEGER, Nullable) — Team limits (Competitions)
*   `prize_pool` (VARCHAR, Nullable) — Cash/Reward details
*   `speaker` (VARCHAR, Nullable) — Speaker details (Seminars)

#### Event Registrations Table (`event_registrations`)
*   `id` (INTEGER, PK, Autoincrement)
*   `event_id` (INTEGER, FK -> `events.id`, Not Null)
*   `student_id` (INTEGER, FK -> `users.id`, Not Null)
*   `registered_at` (DATETIME, Default current_timestamp)
*   `status` (VARCHAR, Default 'Registered') — `'Registered' | 'Cancelled'`

#### Notifications Table (`notifications`)
*   `id` (INTEGER, PK, Autoincrement)
*   `recipient_id` (INTEGER, FK -> `users.id`, Not Null)
*   `title` (VARCHAR, Not Null)
*   `message` (TEXT, Not Null)
*   `type` (VARCHAR, Not Null) — `'RequestStatus' | 'NewEvent' | 'EventUpdate' | 'RegistrationClosing' | 'Reminder'`
*   `related_type` (VARCHAR, Nullable) — `'Request' | 'Event'`
*   `related_id` (INTEGER, Nullable)
*   `read` (BOOLEAN, Default False)
*   `created_at` (DATETIME, Default current_timestamp)
*   *Legacy fields (for backward compatibility):*
    *   `student_id` (INTEGER, FK -> `users.id`, Nullable)
    *   `query` (TEXT, Nullable)
    *   `status` (VARCHAR, Default 'Pending') — `'Pending' | 'Read'`

#### Admin Audit Logs Table (`audit_logs`)
*   `id` (INTEGER, PK, Autoincrement)
*   `admin_id` (INTEGER, FK -> `users.id`, Not Null)
*   `action` (VARCHAR, Not Null) — Description (e.g. `"Approved Request #42"`)
*   `module` (VARCHAR, Not Null) — `'Requests' | 'Events' | 'Users' | 'Settings'`
*   `target_type` (VARCHAR, Not Null) — `'Request' | 'Event' | 'User'`
*   `target_id` (INTEGER, Not Null)
*   `previous_value` (TEXT, Nullable) — JSON string snapshot before action
*   `new_value` (TEXT, Nullable) — JSON string snapshot after action
*   `timestamp` (DATETIME, Default current_timestamp)

---

## 2. API Gateways & Routing (FastAPI)
The backend expose standard REST resources under `/api/v1` routes:

### Authentication & Profiles
*   `POST /auth/register` — Standard student registration (forces role to `Student`).
*   `POST /auth/login` — Returns JWT tokens.
*   `GET /auth/me` — Fetches current user profile details.

### Unified Events
*   `GET /events?category={category}` — Returns published events (Students/Public).
*   `GET /events/{id}` — Detail view of a single event.
*   `GET /admin/events?category={category}` — Returns all events (Admin only).
*   `POST /admin/events` — Create an event (Admin only). Registers audit logs.
*   `PUT /admin/events/{id}` — Edit an event (Admin only). Registers audit logs, dispatches alerts.
*   `DELETE /admin/events/{id}` — Delete an event (Admin only). Registers audit logs, dispatches cancellation notifications.

### Event Registrations
*   `POST /events/{id}/register` — Register student for an event.
*   `DELETE /events/{id}/register` — Cancel registration.
*   `GET /student/event-registrations` — View active event registrations.

### Notifications
*   `GET /notifications` — Fetches user notifications (legacy compatibility support).
*   `PUT /notifications/{id}/read` — Set read status to `True`.
*   `PUT /notifications/read-all` — Sets all unread notifications to read.

### Audit Logging
*   `GET /admin/audit-logs` — Fetches paginated audit logs (Admin only).

---

## 3. Frontend Architecture (React SPA)

### Sidebar Layouts
The application implements Role-Based Access Control (RBAC) in navigation links:

*   **Student Sidebar:**
    *   Dashboard
    *   Events
    *   Notifications
    *   Student Services
    *   Communications
*   **Admin Sidebar:**
    *   Dashboard
    *   Student Requests
    *   Events (Unified panel with Client-Side category tags)
    *   Users
    *   Notifications (Broadcasts builder)
    *   Analytics
    *   Audit Logs
    *   Settings

### Events Filter & Dynamic Creator
*   Filtering is handled using horizontal category selectors inside the Event module.
*   The event creation panel uses a dynamic form structure that expands/collapses inputs (e.g. `team_size` or `speaker`) based on the chosen category type.

---

## 4. Agent Coordination (LangGraph)
*   **Supervisor Routing:** Standard StateGraph routing layers parse student inquiries to query database entries directly.
*   **EventsAgent:** Handles conversational queries regarding upcoming schedules and registration states by executing direct SQL operations on the unified `events` table.
*   **NotificationAgent:** Logs reminders into the `notifications` table utilizing backward compatible fields.

---

## 5. Security & Retention
*   **Upload Safety:** File uploads are limited to 5MB and validated to ensure only `application/pdf` MIME types are allowed.
*   **Audit Log Lifecycle:** Logs older than 90 days are moved to `campus_audit_archive.db`; logs older than 365 days are exported to JSONL format and purged from active storage.
