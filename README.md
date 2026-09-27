# Course Commerce API

Phase 1 provides a local Django REST Framework foundation. PostgreSQL is the only
application database. Business/domain features, JWT, and authentication endpoints
are not included yet.

Phase 2 adds an open development Users API. Authentication and permissions are not
implemented yet.

Phase 3 adds JWT authentication and role-based API permissions.

Phase 4 adds Customer profiles. Registration and profile creation stay separate.

Phase 5 adds category management and public reads of active categories.

Phase 6 adds products and purchasable product items (SKUs).

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
- Login: <http://127.0.0.1:8000/api/v1/auth/login/>
- Current user: <http://127.0.0.1:8000/api/v1/auth/me/>
- Current customer: <http://127.0.0.1:8000/api/v1/customers/me/>
- Categories: <http://127.0.0.1:8000/api/v1/categories/>
- Products: <http://127.0.0.1:8000/api/v1/products/>
- Product items: <http://127.0.0.1:8000/api/v1/product-items/>

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
resulting role is always `customer`. Responses never contain password, `is_staff`,
or `is_superuser`.

## Authentication

`POST /api/v1/auth/login/` accepts email and password, returning JWT access and
refresh tokens. Send access tokens to protected endpoints as `Authorization: Bearer
<access-token>`. `GET /api/v1/auth/me/` requires a valid access token.

Public registration is limited to customer accounts. User listing, retrieval, and
updates require an authenticated user with `role = admin`; this is separate from
Django's `is_staff` and `is_superuser` flags.

## Customers API

Customer registration creates a user account only. An authenticated customer must
create their profile separately with `POST /api/v1/customers/me/`, providing
`name`, `phone`, and `document`. The profile is linked to the authenticated user;
clients cannot choose or change that relationship.

Customer endpoints:

- `GET /api/v1/customers/me/` retrieves the authenticated customer's profile.
- `POST /api/v1/customers/me/` creates that profile once.
- `PATCH /api/v1/customers/me/` updates that profile.
- Admin-role users can list, retrieve, and partially update profiles at
  `/api/v1/customers/` and `/api/v1/customers/{id}/`.

Profiles use UUID identifiers. `user` and `document` are unique. Deletion and full
replacement are not exposed.

## Phase 4 manual checks

After setting `.env` and creating the local PostgreSQL database, run:

```powershell
python manage.py migrate
pytest tests/test_customers.py tests/test_authentication.py -v
ruff check .
python manage.py runserver
```

In Swagger at <http://127.0.0.1:8000/api/docs/>:

1. Register a user, then log in and authorize Swagger with the returned access
   token.
2. Create a profile at `POST /api/v1/customers/me/`; confirm response includes the
   current user's ID and a UUID profile ID.
3. Retrieve it and patch a field at `/api/v1/customers/me/`.
4. Confirm a second creation is rejected, and a customer cannot access the admin
   customer collection.
5. Log in as an API admin and confirm collection retrieval and partial updates.

The existing `customers/migrations/0001_initial.py` creates the customer profile
table. No new migration is expected for this phase.

## Categories API

Anyone can list and retrieve active categories. API admins can also see inactive
categories, create categories, and partially update them. Category names and slugs
are required; slugs are unique and normalized to lowercase. Full replacement and
deletion are not exposed.

Endpoints:

- `GET /api/v1/categories/` lists active categories.
- `GET /api/v1/categories/{id}/` retrieves an active category by UUID.
- `POST /api/v1/categories/` creates a category; API admin role required.
- `PATCH /api/v1/categories/{id}/` partially updates a category; API admin role
  required.

After setting `.env` and creating the local PostgreSQL database, run:

```powershell
python manage.py migrate
ruff check .
python manage.py runserver
```

In Swagger at <http://127.0.0.1:8000/api/docs/>, confirm anonymous users can read
active categories, inactive categories are hidden from them, and an API admin can
create and edit categories. Confirm customer-role users receive `403` for writes.
The migration `categories/migrations/0001_initial.py` creates the category table.

## Products and Product Items API

Public users can list and retrieve active products. Product items are visible only
when both the item and its product are active. API admins can list inactive
records, create resources, and partially update them. Writes require the
`admin` role. Product deletion and full replacement are not exposed.

Endpoints:

- `GET /api/v1/products/` and `GET /api/v1/products/{id}/`
- `POST /api/v1/products/` and `PATCH /api/v1/products/{id}/` (admin only)
- `GET /api/v1/product-items/` and `GET /api/v1/product-items/{id}/`
- `POST /api/v1/product-items/` and `PATCH /api/v1/product-items/{id}/` (admin only)

Products require a category UUID, name, and optional description. Product items
require a product UUID, globally unique SKU, name, and non-negative price with two
decimal places. Both resources use UUID identifiers.

Run migrations and static lint manually:

```powershell
python manage.py migrate
pytest tests/test_products.py -v
ruff check .
python manage.py runserver
```

In Swagger at <http://127.0.0.1:8000/api/docs/>, check public active filtering,
UUID relationships, duplicate SKU and negative-price validation, pagination,
admin-only writes, and rejected `PUT`/`DELETE` methods. The migration
`products/migrations/0001_initial.py` creates both tables.
