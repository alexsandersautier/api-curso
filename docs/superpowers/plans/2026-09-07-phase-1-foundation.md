# Phase 1 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a root-layout Django REST Framework foundation using PostgreSQL, OpenAPI documentation, a minimal email-based custom user, and a health endpoint.

**Architecture:** `core` owns Django configuration and root routes; `users` owns only the minimal custom user required before first migration. A DRF function view provides the versioned health route and drf-spectacular generates documentation from registered URLs.

**Tech Stack:** Python 3.13, Django, Django REST Framework, PostgreSQL, psycopg, django-environ, drf-spectacular, pytest, pytest-django, Ruff.

**Spec:** `docs/superpowers/specs/2026-09-07-phase-1-foundation-design.md`

## Global Constraints

- Keep `manage.py`, `core/`, `users/`, and future domain apps at repository root.
- PostgreSQL is only application database; do not configure SQLite or Docker.
- Do not add domain apps, JWT, authentication endpoints, roles, permissions, serializers, views, or business logic.
- `users.User` must remove `username`, authenticate with unique `email`, and support `create_user`, `create_superuser`, and `createsuperuser` without a username.
- Provide `/api/schema/`, `/api/docs/`, `/api/redoc/`, and `GET /api/v1/health/`.
- Do not run PostgreSQL management, development server, full pytest suite, or repeated migration/test loops automatically.

---

### Task 1: Package and environment foundation

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `pytest.ini`
- Create: `README.md`

**Interfaces:**
- Consumes: documented environment variables.
- Produces: editable install with `dev` extra and pytest configured for `core.settings`.

- [ ] **Step 1: Define package metadata and dependencies**

Create `pyproject.toml` using setuptools with these runtime dependencies:

```toml
dependencies = [
  "Django>=5.2,<6.0",
  "djangorestframework>=3.15,<4.0",
  "django-environ>=0.11,<1.0",
  "drf-spectacular>=0.28,<1.0",
  "psycopg[binary]>=3.2,<4.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-django>=4.9", "ruff>=0.9"]
```

- [ ] **Step 2: Add environment and test configuration**

Create `.env.example` containing every variable with safe placeholder values:

```dotenv
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
POSTGRES_DB=api_curso
POSTGRES_USER=api_curso
POSTGRES_PASSWORD=replace-with-a-local-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Create `pytest.ini`:

```ini
[pytest]
DJANGO_SETTINGS_MODULE = core.settings
python_files = test_*.py *_tests.py
```

- [ ] **Step 3: Add ignores, Ruff rules, and Windows README**

Ignore `.env`, virtual environments, Python bytecode, pytest cache, Ruff cache, coverage artifacts, and local `db.sqlite3` artifacts. Configure Ruff `target-version = "py313"` and `select = ["E", "F", "I"]`. Document exact Windows commands for venv, editable install, `.env` creation, PostgreSQL database/user creation expectation, migrations, server, pytest, Ruff, and Swagger URL.

### Task 2: Django configuration and OpenAPI routes

**Files:**
- Create: `manage.py`
- Create: `core/__init__.py`
- Create: `core/settings.py`
- Create: `core/urls.py`
- Create: `core/asgi.py`
- Create: `core/wsgi.py`

**Interfaces:**
- Consumes: `.env` variables and installed packages from Task 1.
- Produces: `core.settings`, PostgreSQL Django settings, DRF defaults, and documentation routes.

- [ ] **Step 1: Configure settings**

Load `.env` from repository root with `django-environ`. Configure `DATABASES["default"]` with `django.db.backends.postgresql` and `POSTGRES_*` variables. Include `rest_framework`, `drf_spectacular`, and `users` in `INSTALLED_APPS`; set `AUTH_USER_MODEL = "users.User"`; use UTC timezone. Configure DRF with `DEFAULT_SCHEMA_CLASS = "drf_spectacular.openapi.AutoSchema"`, JSON and browsable renderers, and `PageNumberPagination` with page size 20. Do not configure JWT or custom permissions.

- [ ] **Step 2: Configure schema metadata and root URLs**

Set `SPECTACULAR_SETTINGS` title to `Course Commerce API`, description to `Local REST API for commerce and order management.`, and version to `1.0.0`. Register `SpectacularAPIView`, `SpectacularSwaggerView`, and `SpectacularRedocView` at `/api/schema/`, `/api/docs/`, and `/api/redoc/`. Reserve `/api/v1/` for application URLs.

### Task 3: Minimal email custom user and migration

**Files:**
- Create: `users/__init__.py`
- Create: `users/apps.py`
- Create: `users/models.py`
- Create: `users/admin.py`
- Create: `users/migrations/__init__.py`
- Create: `users/migrations/0001_initial.py`

**Interfaces:**
- Consumes: `AUTH_USER_MODEL = "users.User"` from Task 2.
- Produces: `UserManager.create_user(email, password=None, **extra_fields)`, `UserManager.create_superuser(email, password=None, **extra_fields)`, and `User` with `email` as `USERNAME_FIELD`.

- [ ] **Step 1: Implement `UserManager`**

Subclass `BaseUserManager`. Normalize and require `email` in `create_user`; set password via `set_password`; save using `self._db`. In `create_superuser`, set and enforce `is_staff=True` and `is_superuser=True`, then call `create_user`.

- [ ] **Step 2: Implement minimal `User`**

Subclass `AbstractUser`. Override `email` with `models.EmailField(unique=True)`, set `username = None`, set `USERNAME_FIELD = "email"`, `REQUIRED_FIELDS = []`, and attach `objects = UserManager()`. Register user model with `UserAdmin` without username fields so Django admin and `python manage.py createsuperuser` prompt for email and password only.

- [ ] **Step 3: Generate initial migration**

After dependencies and `.env` are present, run `python manage.py makemigrations users` once. Review that `users/migrations/0001_initial.py` creates only the custom user table and Django's standard group/permission relations; retain its generated output.

### Task 4: Health contract tests and endpoint

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_health.py`
- Create: `core/api.py`
- Modify: `core/urls.py`

**Interfaces:**
- Consumes: DRF config from Task 2.
- Produces: `health_check(request) -> Response` at `/api/v1/health/`.

- [ ] **Step 1: Write failing route tests**

In `tests/test_health.py`, add real-client tests:

```python
import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_endpoint_returns_ok_status():
    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_openapi_schema_endpoint_is_available():
    response = APIClient().get("/api/schema/")

    assert response.status_code == 200
    assert "openapi" in response.json()
```

The first test catches removal, wrong route, wrong status code, or changed health payload. The second catches a missing or broken schema route.

- [ ] **Step 2: Run focused tests only if user authorizes runtime validation**

Run: `pytest tests/test_health.py -v`

Expected before implementation: route failures because `/api/v1/health/` is not registered.

- [ ] **Step 3: Implement minimal DRF health view**

Create `core/api.py`:

```python
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response


@extend_schema(
    responses={200: {"type": "object", "properties": {"status": {"type": "string"}}}}
)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "ok"})
```

Include `path("api/v1/health/", health_check, name="health-check")` in `core/urls.py`.

- [ ] **Step 4: Run focused tests only if user authorizes runtime validation**

Run: `pytest tests/test_health.py -v`

Expected: both tests pass.

### Task 5: Static review and handoff

**Files:**
- Verify: all files above.

**Interfaces:**
- Consumes: Phase 1 implementation.
- Produces: manual-command handoff with expected results.

- [ ] **Step 1: Inspect scope**

Review package tree and source for excluded Phase 2 features. Confirm only `users` domain-adjacent code exists and it contains model, manager, admin registration, and migration only.

- [ ] **Step 2: Run only lightweight static verification**

Run: `python -m compileall core users tests` and `ruff check .` only if dependencies are installed. Do not run database management, a development server, or full pytest suite.

- [ ] **Step 3: Hand off manual commands**

Provide Windows commands for installation, `.env` setup, `makemigrations users` when migration is not already supplied, `migrate`, `createsuperuser`, focused tests, Ruff, and `runserver`; include expected URLs and response payload.
