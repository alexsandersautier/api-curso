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
    assert b"openapi:" in response.content
