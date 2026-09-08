# Phase 1 Foundation Design

## Scope

Create only the local Django REST Framework project foundation. PostgreSQL remains
the application database. No business-domain apps or features are created, except
the minimal custom `users.User` model required to set `AUTH_USER_MODEL` before the
first migration.

## Project Layout

Project packages live at repository root:

```text
manage.py
core/
users/
tests/
```

`core` owns settings, root URL routing, and ASGI/WSGI entry points. `users` owns the
minimal custom user model only. Later domain apps will also live at the repository
root. No `products` app is created in this phase.

## Configuration and Dependencies

`pyproject.toml` provides runtime dependencies: Django, Django REST Framework,
psycopg, django-environ, and drf-spectacular. Its `dev` extra provides pytest,
pytest-django, and Ruff.

Settings load values from `.env` and require PostgreSQL connection variables. The
database engine is `django.db.backends.postgresql`; SQLite is not configured as the
application database. `.env.example` documents every required variable, while
`.gitignore` excludes `.env`, virtual environments, caches, and generated local
files.

## HTTP Surface

DRF global settings use JSON and browsable API renderers, sensible pagination, and
no custom authentication or permission scheme. drf-spectacular generates OpenAPI.
The public documentation routes are `/api/schema/`, `/api/docs/`, and
`/api/redoc/`.

`GET /api/v1/health/` is a DRF function view returning `{"status": "ok"}`. It is
documented in generated OpenAPI with a response schema.

## Custom User Foundation

`users.User` subclasses Django's `AbstractUser`, removes username, and uses a
unique email as `USERNAME_FIELD`. It contains no role model, API serializer, view,
authentication endpoint, or business workflow. This is the narrowest safe point to
set `AUTH_USER_MODEL` before migrations.

## Testing and Quality

pytest-django uses `core.settings`. Tests call the real Django/DRF routes and check
the health payload/status plus schema endpoint availability. Ruff targets Python
3.13 with practical error, import, and formatting-adjacent checks.

## Manual Validation

The user creates `.env`, creates a local PostgreSQL database matching it, installs
dependencies, then runs `python manage.py makemigrations users`, `python manage.py
migrate`, `pytest`, `ruff check .`, and `python manage.py runserver`. Swagger loads
at `http://127.0.0.1:8000/api/docs/` and the health response loads at
`http://127.0.0.1:8000/api/v1/health/`.

## Deliberate Exclusions

No JWT, login, refresh, domain models, products app, carts, orders, Docker, Celery,
Redis, generic service/repository framework, or full test-suite execution by the
agent.
