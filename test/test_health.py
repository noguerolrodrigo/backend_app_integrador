"""Tests básicos del backend"""


def test_healthcheck(client):
    """GET / debe retornar 200 y mensaje de activo"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Backend activo"


def test_app_title(client):
    """La app debe tener título y versión en OpenAPI"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert data["info"]["title"] == "API Parcial FastAPI + SQLModel"
    assert data["info"]["version"] == "1.0.0"
