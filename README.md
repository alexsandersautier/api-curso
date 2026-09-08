# Course Commerce API

Phase 1 provides a local Django REST Framework foundation. PostgreSQL is the only
application database. Business/domain features, JWT, and authentication endpoints
are not included yet.

Phase 2 adds an open development Users API. Authentication and permissions are not
implemented yet.

## Requirements

- Python 3.13
- Local PostgreSQL server
- A PostgreSQL database and user matching `.env`
- A PostgreSQL maintenance database named `postgres`, accessible to the configured
  application user; Django uses it to create and remove test databases.

Create the database and user with your local PostgreSQL administration tool or
`psql`. Grant the configured user access to the configured database.

## Windows setup

```powershell
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -e ".[dev]"
copy .env.example .env
```

Edit `.env` with a real `DJANGO_SECRET_KEY` and local PostgreSQL credentials.

## Database and server

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`createsuperuser` prompts for email and password; it does not request a username.

## URLs

- Swagger UI: <http://127.0.0.1:8000/api/docs/>
- ReDoc: <http://127.0.0.1:8000/api/redoc/>
- OpenAPI schema: <http://127.0.0.1:8000/api/schema/>
- Health: <http://127.0.0.1:8000/api/v1/health/>
- Users: <http://127.0.0.1:8000/api/v1/users/>

Expected health response:

```json
{"status": "ok"}
```

## Tests and lint

```powershell
pytest tests/test_health.py -v
ruff check .
```

## Users API

Available development endpoints:

- `POST /api/v1/users/`
- `GET /api/v1/users/`
- `GET /api/v1/users/{id}/`
- `PATCH /api/v1/users/{id}/`

User creation requires `email` and a password of at least eight characters. The
optional role is `customer` (default) or `admin`. Responses never contain password,
`is_staff`, or `is_superuser`.
