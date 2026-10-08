# CampusOS API Endpoint Map

## 1. Authentication & Profiles
*   `POST /auth/register` — Standard student registration. No auth required.
*   `POST /auth/login` — Returns authentication credentials. No auth required.
*   `GET /auth/me` — Fetches current user profile. Auth: Student or Admin.

## 2. Student Services & Requests
*   `GET /student/requests` — Returns requests filed by the logged-in student. Auth: Student.
*   `POST /student/requests` — Creates a request. Auth: Student.
*   `GET /student/requests/{request_id}/history` — Returns request transition log. Auth: Student (Owner) or Admin.
*   `GET /admin/requests` — Returns all student requests. Auth: Admin.
*   `GET /admin/requests/{request_id}` — Returns a request and its full history. Auth: Admin.
*   `PUT /admin/requests/{request_id}` — Updates a request status and appends a transition note. Auth: Admin.

## 3. Events & Registrations
*   `GET /events` — Returns all published events. No auth required.
*   `GET /events/{id}` — Returns single published event details. No auth required.
*   `POST /events/{id}/register` — Register student for an event. Auth: Student.
*   `DELETE /events/{id}/register` — Cancel registration. Auth: Student.
*   `GET /student/event-registrations` — View active registrations for the current student. Auth: Student.
*   `GET /admin/events` — Returns all events (drafts and published). Auth: Admin.
*   `POST /admin/events` — Creates a new event. Auth: Admin.
*   `PUT /admin/events/{id}` — Updates event properties. Auth: Admin.
*   `DELETE /admin/events/{id}` — Deletes an event. Auth: Admin.

## 4. Notifications & Live Feed
*   `GET /notifications` — Fetches read/unread notifications for the current user. Auth: Student or Admin.
*   `PUT /notifications/{id}/read` — Sets notification read status to True. Auth: Student or Admin (Owner).
*   `PUT /notifications/read-all` — Marks all unread notifications as read. Auth: Student or Admin.
*   `WS /ws/notifications/{user_id}` — Persistent WebSocket connection for push notifications. Auth: Connection checks matches token query parameter.

## 5. Administrative AI Intelligence
*   `POST /admin/complaints/cluster` — Trigger complaint grouping. Auth: Admin.
*   `GET /admin/clusters` — Retrieve semantic complaint clusters. Auth: Admin.
*   `POST /admin/clusters/{cluster_id}/broadcast` — Broadcast systemic resolution. Auth: Admin.
*   `GET /admin/audit-logs` — Paginated audit logging. Auth: Admin.

## 6. AI Chat Gateway
*   `GET /ask` — Main AI chat interface. Routes requests to agents. Auth: Student or Admin.
