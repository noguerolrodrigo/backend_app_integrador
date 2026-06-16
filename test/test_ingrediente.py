"""Tests CRUD del módulo Ingrediente"""

BASE_URL = "/ingredientes/"


def test_crear_ingrediente(client, auth_headers):
    """POST /ingredientes/ debe crear un ingrediente (201 Created)"""
    response = client.post(BASE_URL, json={
        "nombre": "Queso Mozzarella",
        "descripcion": "Queso fresco",
        "es_alergeno": False,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Queso Mozzarella"
    assert data["es_alergeno"] is False
    assert "id" in data


def test_crear_ingrediente_alergeno(client, auth_headers):
    """POST /ingredientes/ con es_alergeno=True"""
    response = client.post(BASE_URL, json={
        "nombre": "Maní",
        "descripcion": "Alérgeno común",
        "es_alergeno": True,
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["es_alergeno"] is True


def test_listar_ingredientes(client, auth_headers):
    """GET /ingredientes/ debe listar ingredientes"""
    client.post(BASE_URL, json={
        "nombre": "Tomate", "descripcion": "Rojo", "es_alergeno": False,
    }, headers=auth_headers)
    client.post(BASE_URL, json={
        "nombre": "Lechuga", "descripcion": "Verde", "es_alergeno": False,
    }, headers=auth_headers)
    response = client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    nombres = [i["nombre"] for i in data]
    assert "Tomate" in nombres
    assert "Lechuga" in nombres


def test_obtener_ingrediente_por_id(client, auth_headers):
    """GET /ingredientes/{id} debe retornar un ingrediente"""
    created = client.post(BASE_URL, json={
        "nombre": "Cebolla", "descripcion": "Morada", "es_alergeno": False,
    }, headers=auth_headers).json()
    response = client.get(f"{BASE_URL}{created['id']}")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Cebolla"


def test_obtener_ingrediente_inexistente(client):
    """GET /ingredientes/{id} con id inexistente debe retornar 404"""
    response = client.get(f"{BASE_URL}99999")
    assert response.status_code == 404


def test_actualizar_ingrediente(client, auth_headers):
    """PUT /ingredientes/{id} debe actualizar el ingrediente"""
    created = client.post(BASE_URL, json={
        "nombre": "Pimiento", "descripcion": "Verde", "es_alergeno": False,
    }, headers=auth_headers).json()
    response = client.put(f"{BASE_URL}{created['id']}", json={
        "descripcion": "Pimiento rojo asado",
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["descripcion"] == "Pimiento rojo asado"


def test_eliminar_ingrediente(client, auth_headers):
    """DELETE /ingredientes/{id} debe hacer soft delete (204) y GET devuelve 404"""
    created = client.post(BASE_URL, json={
        "nombre": "Orégano", "descripcion": "Seco", "es_alergeno": False,
    }, headers=auth_headers).json()
    delete_resp = client.delete(f"{BASE_URL}{created['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204
    get_resp = client.get(f"{BASE_URL}{created['id']}")
    assert get_resp.status_code == 404


def test_ingrediente_soft_delete_no_aparece_en_lista(client, auth_headers):
    """Ingrediente eliminado (soft delete) no aparece en GET /ingredientes/"""
    created = client.post(BASE_URL, json={
        "nombre": "Albahaca", "descripcion": "Fresca", "es_alergeno": False,
    }, headers=auth_headers).json()
    client.delete(f"{BASE_URL}{created['id']}", headers=auth_headers)
    lista = client.get(BASE_URL).json()
    ids = [i["id"] for i in lista]
    assert created["id"] not in ids


def test_crear_con_stock_cantidad(client, auth_headers):
    """POST /ingredientes/ con stock_cantidad=50 debe persistir el valor"""
    response = client.post(BASE_URL, json={
        "nombre": "Harina", "descripcion": "000", "es_alergeno": False, "stock_cantidad": 50,
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["stock_cantidad"] == 50


def test_restaurar_ingrediente(client, auth_headers):
    """DELETE → POST /{id}/restaurar → GET devuelve 200 con el ingrediente restaurado"""
    created = client.post(BASE_URL, json={
        "nombre": "Azúcar", "descripcion": "Blanca", "es_alergeno": False,
    }, headers=auth_headers).json()
    client.delete(f"{BASE_URL}{created['id']}", headers=auth_headers)
    restaurar_resp = client.post(f"{BASE_URL}{created['id']}/restaurar", headers=auth_headers)
    assert restaurar_resp.status_code == 200
    assert restaurar_resp.json()["id"] == created["id"]
    get_resp = client.get(f"{BASE_URL}{created['id']}")
    assert get_resp.status_code == 200
