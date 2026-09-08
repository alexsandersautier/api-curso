# Phase 2 Users Implementation Plan

> **For agentic workers:** Execute inline task-by-task. Tests are written before endpoint implementation; the user performs runtime commands manually.

**Goal:** Add the Users REST API without authentication or unrelated domain features.

**Architecture:** `users.models` owns role and timestamps. Serializers normalize and validate input, while a `ModelViewSet` selects create, update, and response serializers. A DRF router exposes only list, retrieve, create, and partial-update actions under `/api/v1/users/`.

**Tech Stack:** Django, Django REST Framework, PostgreSQL, drf-spectacular, pytest-django.

**Spec:** User request for Phase 2, 2026-09-07.

## Global Constraints

- Preserve existing integer `User` primary key: `users/0001_initial.py` already defines `BigAutoField`, and Phase 1 migration has been applied.
- Create a new migration; never edit `0001_initial.py`.
- Do not add JWT, permissions, login, DELETE, PUT, roles beyond `customer` and `admin`, or other domain apps.
- Do not run migrations, pytest, Ruff, PostgreSQL management, or development server automatically.

### Task 1: Extend User persistence

**Files:** `users/models.py`, `users/admin.py`, `users/migrations/0002_user_role_user_created_at_user_updated_at.py`

- [ ] Add `UserRole(models.TextChoices)` with `CUSTOMER = "customer"` and `ADMIN = "admin"`.
- [ ] Add `role`, `created_at`, and `updated_at` fields; update admin display/form fields.
- [ ] Create a new additive migration with those three fields only.

### Task 2: Write API contract tests

**Files:** `tests/test_users.py`, `tests/test_health.py`

- [ ] Cover create, hashed password, omitted sensitive fields, normalization, duplicate/invalid email, short password, valid/default/invalid role, pagination, retrieve/404, allowed PATCH fields, blocked sensitive PATCH fields, 405 DELETE, health, and schema routes.

### Task 3: Add serializers, routes, and ViewSet

**Files:** `users/serializers.py`, `users/views.py`, `users/urls.py`, `core/urls.py`

- [ ] Normalize email with `strip().lower()` before serializer uniqueness validation/persistence.
- [ ] Hash new passwords through `User.objects.create_user()`.
- [ ] Allow only email, role, and is_active in partial updates.
- [ ] Use `ModelViewSet`, limit methods to `get`, `post`, `patch`, and tag OpenAPI operations as `Users`.
- [ ] Register router path `users` beneath `/api/v1/`.

### Task 4: Documentation and handoff

**Files:** `README.md`

- [ ] Document Users endpoints and Phase 2 manual validation commands.
- [ ] Report migration review, Swagger checks, scope boundaries, and manual runtime commands.
