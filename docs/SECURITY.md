# CampusOS Security Specification

This document details the security controls, validation rules, and threat models for the CampusOS application.

## 1. Authentication & Token Storage
* **Current State**: JWT tokens are stored in `localStorage` and sent via `Authorization: Bearer <token>` headers.
* **Target State (Harden)**:
  * Transition to **HttpOnly, Secure, SameSite=Strict Cookies** for token storage to mitigate Cross-Site Scripting (XSS) token theft.
  * Tokens must contain `sub` (User ID), `role` (Admin/Student), and `exp` (Expiration) properties.
  * Token verification must reject expired or signature-mismatched keys.

## 2. Authorization & RBAC
* **Roles**: `Student` and `Admin`.
* **Resource Ownership**:
  * Every endpoint accessing resources (Requests, Notifications, Registrations) must validate ownership server-side.
  * Example: `request.student_id == current_user.id` or `current_user.role == 'Admin'`.
  * Do not trust client-supplied user IDs. Always resolve identity from the verified session context.

## 3. Rate Limiting Rules
* To protect backend services and AI credits, rate limiting will be enforced at:
  * `/auth/login` and `/auth/register`: 10 requests per minute.
  * `/ask` (AI Gateway): 5 queries per minute.
  * `/student/requests` (Request filing): 10 submissions per minute.
  * `/events/{id}/register` (Event booking): 15 bookings per minute.
* Limits are key-mapped dynamically by Client IP and User ID.

## 4. File Upload Validation
* **MIME Verification**: Restrict uploads strictly to `application/pdf` MIME type.
* **Size Boundary**: Enforce a hard 5MB size limit.
* **Filename Sanitization**: Strip non-alphanumeric characters (except dots and dashes) to prevent path traversal vulnerability (`../../path`).
* **Signature Check**: Check magic numbers (`%PDF-`) at the beginning of the file stream to prevent extensions spoofing.

## 5. AI Input Safety (Prompt Injection Defense)
* **Untrusted Input**: Treat all conversational user inputs as raw strings.
* **No Direct DB Access**: AI must never generate or execute raw SQL commands.
* **Schema Validation**: All AI intent actions mapped to backend services must pass strict Pydantic parsing and service-level validation.
