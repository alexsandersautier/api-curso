# Course Commerce API

Course Commerce API uses Django REST Framework and PostgreSQL. Implemented
phases cover foundation, users, JWT authentication, customers, categories, products
and product items, inventory, customer carts, and order checkout.

## Requirements

- Python 3.13
- PostgreSQL server (local for development, Render PostgreSQL for deployment)
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

## Deploy to Render

The root `render.yaml` defines a public Render web service and PostgreSQL
database. To deploy, push this repository to GitHub, then in Render choose
**New → Blueprint**, connect the repository, review the Blueprint, and apply it.
Render generates `DJANGO_SECRET_KEY`, sets production mode, connects `DATABASE_URL`,
collects static files, runs migrations at service startup, and starts Gunicorn.
The health check uses `/api/v1/health/`.

The included Blueprint uses free plans to make the course API easy to publish.
Render free web services can sleep while idle, and free PostgreSQL databases expire
after 30 days. Upgrade the database plan before expiration if its data must persist.
The API endpoints are public where their permissions allow; admin writes still
require an admin-role account. Render Shell is unavailable on free web services, so
create the initial account with a paid web service Shell or run
`python manage.py createsuperuser` locally with Render PostgreSQL's external
connection URL set as `DATABASE_URL`.

`createsuperuser` prompts for email and password; it does not request a username.

### One-time admin bootstrap

For a one-time bootstrap through the deployed API, set `ADMIN_BOOTSTRAP_TOKEN` in
the Render service environment to a random value of at least 32 characters. After
the service restarts, send a `POST` request to
`https://<your-service>.onrender.com/api/v1/auth/bootstrap-admin/` with the token
in the `X-Admin-Bootstrap-Token` header and a strong password in the JSON body:

```json
{"password": "<a-strong-password>"}
```

The endpoint creates `admin@admin.com` as a Django superuser, works only while no
admin-role account exists, and is excluded from the OpenAPI schema. Remove
`ADMIN_BOOTSTRAP_TOKEN` from Render immediately after successful creation. The
endpoint then returns `404` and cannot be used again after an admin account exists.
Do not use `admin` as the password; Django's password validators reject weak
passwords.

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
- Inventory: <http://127.0.0.1:8000/api/v1/inventory/>
- Current cart: <http://127.0.0.1:8000/api/v1/carts/me/>
- Cart items: <http://127.0.0.1:8000/api/v1/cart-items/>
- Orders: <http://127.0.0.1:8000/api/v1/orders/>

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
or `is_superuser`. `python manage.py createsuperuser` assigns `role = admin` along
with Django's staff and superuser flags, giving the initial account access to API
backoffice endpoints.

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

## Inventory API

Each inventory record belongs to one product item. API admins can list all
records, create stock records, and update quantity. Public reads show availability
for active product items with active parent products; responses expose `in_stock`
but never the exact quantity. Only admins can view or change exact quantities.

Endpoints:

- `GET /api/v1/inventory/` and `GET /api/v1/inventory/{id}/`
- `POST /api/v1/inventory/` and `PATCH /api/v1/inventory/{id}/` (admin only)

Run migrations and checks manually:

```powershell
python manage.py migrate
pytest tests/test_inventory.py -v
ruff check .
python manage.py runserver
```

In Swagger at <http://127.0.0.1:8000/api/docs/>, confirm public responses contain
`in_stock` without `quantity`, admin responses include exact quantity, zero stock
returns `in_stock: false`, and duplicate ProductItem inventory is rejected. Check
admin-only writes and that `PUT`/`DELETE` return `405`. The migration
`inventory/migrations/0001_initial.py` creates the inventory table.

## Cart API

An authenticated customer with a customer profile can create one cart at
`POST /api/v1/carts/me/` and retrieve it at `GET /api/v1/carts/me/`. Cart items are
listed and added at `/api/v1/cart-items/`, updated with `PATCH`, or removed with
`DELETE /api/v1/cart-items/{id}/`. Every item belongs to the authenticated
customer's cart; clients cannot set the cart or change the product item after
creation. Duplicate product items are rejected; patch the existing item's quantity
instead.

Creation and quantity updates require an active product item, an inventory record,
and enough current stock. Cart contents do not reserve stock. Unit prices, subtotals,
and cart totals use the current product item price and can change before order
creation.

Run the migration and checks manually:

```powershell
python manage.py migrate
pytest tests/test_carts.py -v
ruff check .
python manage.py runserver
```

In Swagger, create a customer account and profile, authorize with its JWT, create
one cart, add an in-stock product item, update its quantity, and remove it. Confirm
other customers cannot see its cart items, unavailable stock and duplicate items
are rejected, and the cart total reflects current prices. Migration
`carts/migrations/0001_initial.py` creates the cart tables.

## Orders API

Authenticated customers with a profile can create an order with an empty-body
`POST /api/v1/orders/`. Checkout uses the customer's cart, records each ProductItem
price and subtotal, validates current availability, decrements inventory, and clears
the cart in one database transaction. A stock or availability conflict returns
`409`; an empty cart returns `400`. Customers can list and retrieve only their own
orders. API admins can list and retrieve orders across customers and change only
the status with `PATCH /api/v1/orders/{id}/`; valid statuses are `pending`,
`confirmed`, `cancelled`, and `completed`. Customers cannot update order status.

Run the migration and checks manually:

```powershell
python manage.py migrate
pytest tests/test_orders.py tests/test_users.py -v
ruff check .
python manage.py runserver
```

In Swagger, add two items to a customer's cart and submit an empty-body checkout.
Confirm the returned order contains historical unit prices/subtotals, stock falls
by each ordered quantity, and the cart is empty. Change a ProductItem price after
checkout and confirm the order prices stay unchanged. Try empty carts, insufficient
stock, inactive products, and another customer's order IDs. As API admin, confirm
all orders are visible and only `status` can be patched; as customer, confirm status
updates return `403`. Migration `orders/migrations/0001_initial.py` creates the
order tables. This phase adds no migration.
