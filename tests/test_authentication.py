import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

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


def login(api_client, email="customer@test.com", password="12345678"):
    return api_client.post(
        "/api/v1/auth/login/", {"email": email, "password": password}, format="json"
    )


@pytest.mark.django_db
def test_login_returns_access_and_refresh_without_user_data(api_client, customer_user):
    response = login(api_client)

    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data
    assert "password" not in response.data
    assert "email" not in response.data


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("email", "password"),
    [("customer@test.com", "wrong-password"), ("unknown@test.com", "12345678")],
)
def test_login_rejects_invalid_credentials(api_client, customer_user, email, password):
    response = login(api_client, email, password)

    assert response.status_code == 401
    assert "detail" in response.data


@pytest.mark.django_db
def test_login_rejects_inactive_user(api_client, customer_user):
    customer_user.is_active = False
    customer_user.save()

    response = login(api_client)

    assert response.status_code == 401


@pytest.mark.django_db
def test_refresh_returns_new_access_token(api_client, customer_user):
    login_response = login(api_client)

    response = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": login_response.data["refresh"]},
        format="json",
    )

    assert response.status_code == 200
    assert "access" in response.data


@pytest.mark.django_db
def test_refresh_rejects_invalid_token(api_client):
    response = api_client.post(
        "/api/v1/auth/refresh/",
        {"refresh": "invalid"},
        format="json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_me_requires_token_and_returns_safe_current_user(api_client, customer_user):
    unauthenticated_response = api_client.get("/api/v1/auth/me/")
    access_token = login(api_client).data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
    authenticated_response = api_client.get("/api/v1/auth/me/")

    assert unauthenticated_response.status_code == 401
    assert authenticated_response.status_code == 200
    assert authenticated_response.data["id"] == customer_user.pk
    assert authenticated_response.data["email"] == customer_user.email
    assert "password" not in authenticated_response.data
    assert "is_staff" not in authenticated_response.data


@pytest.mark.django_db
def test_users_list_requires_admin_role(api_client, customer_user, admin_user):
    anonymous_response = api_client.get("/api/v1/users/")
    customer_token = login(api_client).data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {customer_token}")
    customer_response = api_client.get("/api/v1/users/")
    admin_token = login(api_client, "admin@test.com").data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    admin_response = api_client.get("/api/v1/users/")

    assert anonymous_response.status_code == 401
    assert customer_response.status_code == 403
    assert admin_response.status_code == 200


@pytest.mark.django_db
def test_only_admin_can_retrieve_and_patch_users(api_client, customer_user, admin_user):
    customer_token = login(api_client).data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {customer_token}")
    customer_retrieve = api_client.get(f"/api/v1/users/{admin_user.pk}/")
    customer_patch = api_client.patch(
        f"/api/v1/users/{admin_user.pk}/", {"is_active": False}, format="json"
    )
    admin_token = login(api_client, "admin@test.com").data["access"]
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {admin_token}")
    admin_retrieve = api_client.get(f"/api/v1/users/{customer_user.pk}/")
    admin_patch = api_client.patch(
        f"/api/v1/users/{customer_user.pk}/", {"is_active": False}, format="json"
    )

    assert customer_retrieve.status_code == 403
    assert customer_patch.status_code == 403
    assert admin_retrieve.status_code == 200
    assert admin_patch.status_code == 200
