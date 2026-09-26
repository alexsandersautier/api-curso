# Products and Product Items API Design

## Goal

Add product catalog resources to the Course Commerce API. A product groups
catalog information and belongs to a category. A product item is a purchasable
SKU that belongs to a product and owns its price.

## Data model

### Product

- UUID primary key.
- Required category relation, protected from deletion while products reference it.
- Required name, optional description, and active status.
- Timezone-aware `created_at` and `updated_at` timestamps.

### ProductItem

- UUID primary key.
- Required product relation, protected from deletion while items reference it.
- Globally unique SKU, required name, decimal price, and active status.
- Timezone-aware `created_at` and `updated_at` timestamps.
- Price must not be negative.

All schema changes use Django migrations. Money uses `DecimalField`; no floating
point values are used.

## API

Use separate plural resources:

- `/api/v1/products/`
- `/api/v1/product-items/`

Both resources support paginated `GET` collection and detail reads, `POST`, and
`PATCH`. `PUT` and `DELETE` are not exposed.

Unauthenticated users and customers can list and retrieve active products and
active product items. A public product item is visible only when both the item
and its parent product are active. API admins can list active and inactive
records, create records, and partially update them. Writes require `role = admin`.

Product writes accept a category UUID. Product item writes accept a product UUID.
Responses include resource UUIDs and relationship identifiers. Product responses
include name, description, active status, and timestamps. Product item responses
include SKU, name, decimal price, active status, and timestamps.

Duplicate SKUs and invalid category/product references return standard DRF
validation errors. Missing or inactive public resources return `404`.

## Structure and documentation

Create a `products` Django app containing models, serializers, views, URLs, admin
registration, and an initial migration. Register the app and routes in the
existing project configuration. Tag generated OpenAPI operations as `Products`
and `Product items`. Update README with endpoints and manual Swagger checks.

## Validation

The implementation should include feature tests for model constraints, serializer
validation, active-record visibility, role permissions, pagination, UUID
relationships, and disallowed methods. The user runs tests and migrations
manually, following the repository execution policy. Ruff remains the permitted
lightweight static check.

## Scope boundaries

This phase adds only products and purchasable product items. It does not add
inventory, stock rules, carts, orders, nested product-item routes, deletion, or
category CRUD changes.
