import uuid

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from customers.models import Customer
from users.models import UserRole

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def customer_user():
    return User.objects.create_user(email="customer@test.com", password="12345678")


@pytest.fixture
def admin_user():
    return User.objects.create_user(
        email="admin@test.com", password="12345678", role=UserRole.ADMIN
    )


def authenticate(api_client, user):
    api_client.force_authenticate(user=user)


def customer_data(**overrides):
    data = {
        "name": "Alex Test",
        "phone": "49999999999",
        "document": "12345678900",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_customer_creates_own_uuid_profile(api_client, customer_user):
    authenticate(api_client, customer_user)
    response = api_client.post("/api/v1/customers/me/", customer_data(), format="json")

    assert response.status_code == 201
    assert response.data["user"] == customer_user.pk
    assert uuid.UUID(response.data["id"])
    assert Customer.objects.get(user=customer_user).name == "Alex Test"


@pytest.mark.django_db
def test_anonymous_cannot_create_customer(api_client):
    response = api_client.post("/api/v1/customers/me/", customer_data(), format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_customer_cannot_select_user_or_create_duplicate(
    api_client, customer_user, admin_user
):
    authenticate(api_client, customer_user)
    selected_user_response = api_client.post(
        "/api/v1/customers/me/", customer_data(user=admin_user.pk), format="json"
    )
    first_response = api_client.post(
        "/api/v1/customers/me/", customer_data(), format="json"
    )
    duplicate_response = api_client.post(
        "/api/v1/customers/me/", customer_data(), format="json"
    )

    assert selected_user_response.status_code == 400
    assert first_response.status_code == 201
    assert duplicate_response.status_code == 400


@pytest.mark.django_db
def test_customer_gets_and_updates_own_profile(api_client, customer_user):
    customer = Customer.objects.create(
        user=customer_user,
        name="Alex Test",
        phone="49999999999",
        document="12345678900",
    )
    authenticate(api_client, customer_user)

    get_response = api_client.get("/api/v1/customers/me/")
    patch_response = api_client.patch(
        "/api/v1/customers/me/", {"phone": "49888888888"}, format="json"
    )
    protected_patch = api_client.patch(
        "/api/v1/customers/me/", {"user": customer_user.pk}, format="json"
    )

    assert get_response.status_code == 200
    assert patch_response.status_code == 200
    assert patch_response.data["phone"] == "49888888888"
    assert protected_patch.status_code == 400
    assert Customer.objects.get(pk=customer.pk).user == customer_user


@pytest.mark.django_db
def test_customer_without_profile_gets_404(api_client, customer_user):
    authenticate(api_client, customer_user)

    assert api_client.get("/api/v1/customers/me/").status_code == 404


@pytest.mark.django_db
def test_customer_cannot_access_admin_customer_endpoints(
    api_client, customer_user, admin_user
):
    customer = Customer.objects.create(
        user=admin_user, name="Admin Customer", phone="", document="11111111111"
    )
    authenticate(api_client, customer_user)

    assert api_client.get("/api/v1/customers/").status_code == 403
    assert api_client.get(f"/api/v1/customers/{customer.pk}/").status_code == 403
    assert api_client.patch(
        f"/api/v1/customers/{customer.pk}/", {"name": "Changed"}, format="json"
    ).status_code == 403


@pytest.mark.django_db
def test_api_admin_manages_customers_with_pagination(
    api_client, customer_user, admin_user
):
    customer = Customer.objects.create(
        user=customer_user, name="Alex Test", phone="", document="12345678900"
    )
    authenticate(api_client, admin_user)

    list_response = api_client.get("/api/v1/customers/")
    retrieve_response = api_client.get(f"/api/v1/customers/{customer.pk}/")
    patch_response = api_client.patch(
        f"/api/v1/customers/{customer.pk}/", {"name": "Alex Updated"}, format="json"
    )

    assert list_response.status_code == 200
    assert list_response.data["count"] == 1
    assert retrieve_response.status_code == 200
    assert patch_response.status_code == 200
    assert patch_response.data["name"] == "Alex Updated"


@pytest.mark.django_db
def test_customer_constraints_prevent_duplicate_user_and_document(
    customer_user, admin_user
):
    Customer.objects.create(
        user=customer_user,
        name="Alex",
        phone="",
        document="12345678900",
    )

    with transaction.atomic(), pytest.raises(IntegrityError):
        Customer.objects.create(
            user=customer_user,
            name="Other",
            phone="",
            document="22222222222",
        )

    with transaction.atomic(), pytest.raises(IntegrityError):
        Customer.objects.create(
            user=admin_user,
            name="Admin",
            phone="",
            document="12345678900",
        )


@pytest.mark.django_db
def test_customer_delete_is_not_exposed(api_client, customer_user, admin_user):
    customer = Customer.objects.create(
        user=customer_user, name="Alex Test", phone="", document="12345678900"
    )
    authenticate(api_client, admin_user)

    response = api_client.delete(f"/api/v1/customers/{customer.pk}/")

    assert response.status_code == 405
