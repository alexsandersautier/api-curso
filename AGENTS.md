
## Project Purpose

Build a local REST API using Django and Django REST Framework for a small commerce/order-management system.

The API must support the business requirements represented by the project diagrams:

* Authentication
* Users
* Customers
* Categories
* Products
* Product Items / Variants
* Inventory / Stock
* Cart
* Cart Items
* Orders
* Order Items
* Admin/backoffice operations
* API documentation with Swagger/OpenAPI

The codebase, identifiers, URLs, models, fields, comments, and documentation must be written in English.

## Core Stack

Use:

* Python 3.13
* Django
* Django REST Framework
* PostgreSQL running locally
* psycopg
* django-environ or equivalent simple environment configuration
* drf-spectacular for OpenAPI/Swagger
* djangorestframework-simplejwt when authentication is implemented
* pytest
* pytest-django
* Ruff

Do not use Docker unless explicitly requested later.
Do not use SQLite as the main application database.

## Architecture

Use a feature/domain-oriented Django structure.

Prefer one Django app per relevant business feature:

```
app/
├── config/
│   ├── settings/
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── users/
│   ├── customers/
│   ├── categories/
│   ├── products/
│   ├── inventory/
│   ├── carts/
│   └── orders/
│
└── manage.py
```

Each feature should keep its own models, serializers, views, urls, tests, and feature-specific logic.

Do not create artificial layers without a concrete need.
Avoid creating generic repositories, generic service frameworks, UnitOfWork abstractions, CQRS, event buses, or DDD infrastructure.
Django ORM is the persistence abstraction.

For non-trivial business workflows, a small `<span>services.py</span>` module inside the feature is acceptable and preferred over placing complex business rules inside views or serializers.
For complex read queries that become reused, a small `<span>selectors.py</span>` module is acceptable.
Do not introduce `<span>services.py</span>` or `<span>selectors.py</span>` merely to satisfy a pattern when the logic is trivial.

## Dependency Direction

Keep HTTP concerns separated from business logic.

Preferred flow:

```
Request
→ DRF View / ViewSet
→ Serializer validation
→ Service when business orchestration is needed
→ Django ORM
→ PostgreSQL
```

Views/ViewSets:

* handle HTTP concerns;
* permissions;
* request/response orchestration;
* status codes;
* call serializers/services;
* must not contain large business workflows.

Serializers:

* validate API input/output;
* serialize models;
* may perform simple create/update behavior;
* must not become a dumping ground for multi-step business workflows.

Services:

* only when useful;
* coordinate multi-model writes;
* own transactional business workflows;
* use `<span>transaction.atomic()</span>` where consistency across multiple writes is required.

Models:

* represent persistence/domain state;
* contain small model-level invariants when appropriate;
* must not know about HTTP.

## API Conventions

All application endpoints must be versioned:

```
/api/v1/
```

Use plural resource names.

Examples:

```
/api/v1/users/
/api/v1/customers/
/api/v1/categories/
/api/v1/products/
/api/v1/inventory/
/api/v1/cart/
/api/v1/orders/
```

Use Django REST Framework conventions and HTTP status codes.

Prefer:

* `<span>GET</span>` for retrieval;
* `<span>POST</span>` for creation/actions;
* `<span>PATCH</span>` for partial updates;
* `<span>DELETE</span>` only where deletion is explicitly allowed.

Use UUID primary keys for public/domain entities unless there is a strong technical reason not to.
Use timezone-aware datetimes.
Use `<span>DecimalField</span>`, never float, for money.
Use pagination for collection endpoints.
Use filters/search/order only when the endpoint needs them.

## Domain Model

### User

Authentication identity.

Expected fields:

* id
* email
* password
* role
* is_active
* is_staff
* created_at
* updated_at

Use a custom Django user model from the beginning.
Email must be the login identifier.
Do not build the project around Django's default username field and later attempt to replace it.

Roles:

```
customer
admin
```

Use Django choices / `<span>TextChoices</span>` unless a stronger reason exists.
Never store plain-text passwords.
Always use Django password hashing APIs.
Never expose password hashes through serializers.

### Customer

Customer profile linked to a User.

Expected relationship:

```
User 1 → 0..1 Customer
```

Potential fields:

* id
* user
* name
* phone
* document
* created_at
* updated_at

### Category

Expected fields:

* id
* name
* slug
* is_active
* created_at
* updated_at

### Product

Represents the main product/group.

Expected fields:

* id
* category
* name
* description
* is_active
* created_at
* updated_at

### ProductItem

Represents a purchasable item / SKU / variant of a Product.

Expected fields:

* id
* product
* sku
* name
* price
* is_active
* created_at
* updated_at

Do not remove ProductItem from the domain unless the user explicitly changes the requirement.

### Inventory

Stock belongs to the purchasable ProductItem.

Expected relationship:

```
ProductItem 1 → 1 Inventory
```

Expected fields:

* id
* product_item
* quantity
* created_at
* updated_at

### Cart

A customer's current shopping cart.

Expected relationship:

```
Customer → Cart → CartItems → ProductItem
```

### CartItem

Expected fields:

* id
* cart
* product_item
* quantity
* created_at
* updated_at

### Order

Expected fields:

* id
* customer
* status
* total
* created_at
* updated_at

Suggested order statuses:

```
pending
confirmed
cancelled
completed
```

Use `<span>TextChoices</span>`.

### OrderItem

Expected fields:

* id
* order
* product_item
* quantity
* unit_price
* subtotal

Always persist the unit price used at the time of purchase.
Do not derive historical order item prices from the current ProductItem price.

## Transaction Rules

Use `<span>transaction.atomic()</span>` for workflows that must succeed or fail as a unit.

For example, final order creation may eventually require:

```
create order
→ create order items
→ validate/reduce inventory
→ clear cart
→ commit
```

If one step fails, the transaction must roll back.
Do not manually scatter partial commits across a multi-step workflow.

## Authentication and Authorization

When authentication is implemented, use JWT with:

* access token;
* refresh token.

Preferred library:

```
djangorestframework-simplejwt
```

Do not invent a custom JWT implementation.
Use DRF permissions.

Expected access model:

* customers can use customer-facing endpoints;
* admins can manage backoffice resources;
* authentication is shared by the API;
* do not create separate authentication systems for app and admin.

Do not expose insecure temporary authentication mechanisms.

## Swagger / OpenAPI

Swagger/OpenAPI is a project requirement.

Use:

```
drf-spectacular
```

Required documentation endpoints:

```
/api/schema/
/api/docs/
/api/redoc/
```

`<span>/api/docs/</span>` must expose Swagger UI.
The generated OpenAPI schema is the source of truth.
Do not manually maintain a separate OpenAPI YAML/JSON file unless explicitly requested.

Every public API endpoint should have useful generated documentation through:

* serializers;
* typed parameters;
* clear response schemas;
* status codes;
* tags;
* concise summaries/descriptions where they add value.

Use `<span>@extend_schema</span>` only when automatic schema generation is insufficient.
Do not over-document trivial endpoints.
When JWT authentication is implemented, Swagger must support authentication through the Authorize button.
Sensitive fields must never appear in response schemas.

## Settings

Use environment variables for configuration.
Maintain:

```
.env
.env.example
```

`<span>.env</span>` must be ignored by Git.

Expected variables include at least:

```
DJANGO_SECRET_KEY=
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

Never commit real secrets.
Prefer split settings only if it improves clarity.
For this local project, avoid unnecessary settings complexity.

## PostgreSQL

PostgreSQL runs locally, not in Docker.
The project must connect through environment configuration.
Do not hardcode database credentials.
Use Django migrations for all schema changes.
Never create or modify database tables manually as part of normal application development.

Typical workflow:

```
python manage.py makemigrations
python manage.py migrate
```

Review generated migrations before considering a feature complete.

## Migrations

Django migrations are the only normal schema-management mechanism.
Every model change that affects schema must have a migration.
Do not edit historical migrations casually after they have been applied.
Do not use raw SQL migrations unless Django migration operations cannot express the requirement cleanly.

## Testing

Use:

* pytest
* pytest-django

Tests should be readable and organized by feature.
Prefer real Django/DRF test behavior over excessive mocking.

At minimum test:

* serializer validation;
* model constraints;
* permissions;
* endpoints;
* business services;
* transactional workflows;
* API status codes;
* sensitive data exclusion.

Use PostgreSQL for behavior that depends on PostgreSQL-specific constraints.
Do not silently replace PostgreSQL with SQLite for the application architecture.

## Code Quality

Use Ruff.
Code must be:

* explicit;
* typed where useful;
* readable;
* small;
* predictable;
* easy for a junior/intermediate developer to follow.

Avoid clever abstractions.
Prefer Django and DRF standard patterns over custom frameworks.
Keep imports clean.
Use descriptive English names.

## Execution Policy

The coding agent implements code but does not automatically perform resource-intensive runtime validation.

Do not automatically run:

* PostgreSQL server management;
* long-running Django development servers;
* full pytest suites;
* repeated migration/test loops;
* heavy or long-running processes.

The user performs runtime validation manually unless explicitly asking the agent to run it.
After each implementation phase, provide the exact commands the user should run manually.
Lightweight static inspection is allowed.
If a command must be run to diagnose a concrete issue, ask before performing resource-intensive execution.

## Local Development

No Docker for now.

The expected local development flow is:

```
Python virtual environment
→ Django / DRF
→ local PostgreSQL
```

Recommended commands should assume a virtual environment.
Windows-friendly commands are preferred when the host is Windows.

Example:

```
py -3.13 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -e ".[dev]"
```

Do not assume WSL or Docker is required.

## Phase Discipline

Implement only the phase explicitly requested by the user.
Do not proactively build future features.

If the current phase is foundation/setup:

* do not create domain models prematurely;
* do not implement JWT prematurely;
* do not implement business features prematurely.

At the end of each phase, report:

1. concise summary;
2. files created/modified;
3. final relevant project tree;
4. migrations created;
5. commands the user should run manually;
6. manual API/Swagger checks to perform;
7. assumptions/decisions;
8. anything requiring attention before the next phase.

Do not continue to the next phase without user approval.

## Recommended Implementation Order

Use this sequence unless the user requests a change:

1. Project foundation
2. PostgreSQL configuration + custom user foundation
3. Users
4. Authentication / JWT
5. Customers
6. Categories
7. Products + ProductItems
8. Inventory
9. Cart + CartItems
10. Orders + OrderItems
11. Admin permissions/backoffice behavior
12. Hardening, filters, pagination, and final tests

Swagger/OpenAPI remains enabled and maintained throughout all phases.

## Scope Control

Do not add the following unless explicitly required:

* Docker
* Celery
* Redis
* Kafka
* GraphQL
* Elasticsearch
* generic repositories
* CQRS
* event sourcing
* microservices
* custom dependency injection frameworks
* custom authentication framework
* premature caching
* premature background jobs

Prefer the simplest Django/DRF solution that correctly satisfies the API requirements.
