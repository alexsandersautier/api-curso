# Cart and Cart Items Implementation Plan

**Goal:** Add one authenticated shopping cart per customer with owned item management.

**Architecture:** Add a `carts` Django app with UUID Cart and CartItem models, database constraints, serializers, and endpoints. Cart item prices and subtotals use current ProductItem prices; stock is checked when creating or changing an item but is not reserved.

**Tech Stack:** Python 3.13, Django, Django REST Framework, PostgreSQL, pytest, drf-spectacular, Ruff.

**Spec:** `AGENTS.md`, Domain Model (Cart, CartItem), API Conventions, Transaction Rules, and Recommended Implementation Order, phase 9.

## Global Constraints

- Keep identifiers, code, comments, URLs, and documentation in English.
- Use PostgreSQL, UUID IDs, versioned plural API paths, serializers, and Django migrations.
- Customer endpoints require authentication and must scope data to the authenticated customer's profile.
- Do not implement orders, payment, or inventory reservation in this phase.
- Runtime tests remain manual unless explicitly requested; run lightweight lint and migration generation only.

---

### Task 1: Cart persistence and constraints

**Files:** Create `carts/apps.py`, `carts/models.py`, migration; modify `core/settings.py`, `pyproject.toml`.

- Add one Cart per Customer, with UUID and timestamps.
- Add CartItem with Cart, ProductItem, positive quantity, UUID and timestamps.
- Add unique `(cart, product_item)` and quantity `> 0` database constraints.
- Register `carts` app and package discovery.
- Generate and review migration.

### Task 2: Customer-owned cart API

**Files:** Create `carts/serializers.py`, `carts/views.py`, `carts/urls.py`; modify `core/urls.py`.

- `GET /api/v1/carts/me/` returns the current customer's cart or 404.
- `POST /api/v1/carts/me/` creates the cart once; second creation returns 400.
- Both methods require authenticated customer role and an existing Customer profile.
- Cart response includes item list, current prices, subtotals, and current total.

### Task 3: Owned cart item management

**Files:** Modify `carts/serializers.py`, `carts/views.py`, `carts/urls.py`; create `tests/test_carts.py`.

- Add/list items through `/api/v1/cart-items/`; patch/delete only the authenticated customer's own items.
- Accept ProductItem and positive quantity on create; allow only quantity on patch.
- Reject inactive product items, missing/insufficient inventory, duplicates, zero/negative quantities, and unknown fields.
- Price and subtotal use the current ProductItem price; cart changes do not reserve inventory.
- Cover auth, ownership, validation, constraints, API responses, Swagger-ready schemas, and HTTP methods.

### Task 4: Documentation and verification

**Files:** Modify `README.md`.

- Document endpoints, assumptions, migration, manual Swagger checks, and tests.
- Run Ruff and `makemigrations --check`; do not run pytest automatically under project execution policy.
- Report exact manual commands and any remaining checks.
