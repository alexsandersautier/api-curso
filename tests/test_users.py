import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


def create_user(**overrides):
    data = {
        "email": "alex@test.com",
        "password": "12345678",
    }
    data.update(overrides)
    return data


@pytest.mark.django_db
def test_create_user_hashes_password_and_hides_sensitive_fields(api_client):
    response = api_client.post("/api/v1/users/", create_user(), format="json")

    assert response.status_code == 201
    assert response.data["email"] == "alex@test.com"
    assert response.data["role"] == "customer"
    assert "password" not in response.data
    assert "is_staff" not in response.data
    assert "is_superuser" not in response.data
    assert User.objects.get(email="alex@test.com").check_password("12345678")


@pytest.mark.django_db
def test_create_user_normalizes_email_and_rejects_duplicate(api_client):
    first_response = api_client.post(
        "/api/v1/users/",
        create_user(email="  Alex@Test.COM  "),
        format="json",
    )
    duplicate_response = api_client.post("/api/v1/users/", create_user(), format="json")

    assert first_response.status_code == 201
    assert first_response.data["email"] == "alex@test.com"
    assert duplicate_response.status_code == 400
    assert "email" in duplicate_response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("payload", "field"),
    [
        (create_user(email="not-an-email"), "email"),
        (create_user(password="short"), "password"),
        (create_user(role="manager"), "role"),
    ],
)
def test_create_user_rejects_invalid_payload(api_client, payload, field):
    response = api_client.post("/api/v1/users/", payload, format="json")

    assert response.status_code == 400
    assert field in response.data


@pytest.mark.django_db
def test_create_user_accepts_admin_role(api_client):
    response = api_client.post(
        "/api/v1/users/",
        create_user(email="admin@test.com", role="admin"),
        format="json",
    )

    assert response.status_code == 201
    assert response.data["role"] == "admin"


@pytest.mark.django_db
def test_list_users_returns_paginated_response(api_client):
    User.objects.create_user(email="one@test.com", password="12345678")
    User.objects.create_user(email="two@test.com", password="12345678")

    response = api_client.get("/api/v1/users/")

    assert response.status_code == 200
    assert response.data["count"] == 2
    assert len(response.data["results"]) == 2


@pytest.mark.django_db
def test_retrieve_user_and_missing_user(api_client):
    user = User.objects.create_user(email="alex@test.com", password="12345678")

    response = api_client.get(f"/api/v1/users/{user.pk}/")
    missing_response = api_client.get("/api/v1/users/999999/")

    assert response.status_code == 200
    assert response.data["id"] == user.pk
    assert missing_response.status_code == 404


@pytest.mark.django_db
def test_patch_allows_email_role_and_active_status(api_client):
    user = User.objects.create_user(email="alex@test.com", password="12345678")

    response = api_client.patch(
        f"/api/v1/users/{user.pk}/",
        {"email": "  NEW@Test.COM ", "role": "admin", "is_active": False},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["email"] == "new@test.com"
    assert response.data["role"] == "admin"
    assert response.data["is_active"] is False


@pytest.mark.django_db
def test_patch_rejects_sensitive_fields(api_client):
    user = User.objects.create_user(email="alex@test.com", password="12345678")

    response = api_client.patch(
        f"/api/v1/users/{user.pk}/",
        {"password": "different-password", "is_staff": True, "is_superuser": True},
        format="json",
    )

    user.refresh_from_db()
    assert response.status_code == 400
    assert user.check_password("12345678")
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_delete_is_not_exposed(api_client):
    user = User.objects.create_user(email="alex@test.com", password="12345678")

    response = api_client.delete(f"/api/v1/users/{user.pk}/")

    assert response.status_code == 405
