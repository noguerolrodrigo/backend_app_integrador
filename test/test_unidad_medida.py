"""Tests CRUD del módulo UnidadMedida"""

BASE_URL = "/api/v1/unidades-medida/"


def test_seed_unidades_presentes(client):
    """GET / debe incluir los 6 registros de seed (kg, g, L, ml, ud, porciones)"""
    response = client.get(BASE_URL)
    assert response.status_code == 200
    simbolos = {u["simbolo"] for u in response.json()}
    assert {"kg", "g", "L", "ml", "ud", "porciones"}.issubset(simbolos)


def test_listar_unidades(client):
    """GET / devuelve lista con al menos 6 elementos (seed)"""
    response = client.get(BASE_URL)
    assert response.status_code == 200
    assert len(response.json()) >= 6


def test_crear_unidad_medida(client, auth_headers):
    """POST / crea una nueva unidad (201)"""
    response = client.post(BASE_URL, json={
        "nombre": "tonelada",
        "simbolo": "t",
        "tipo": "peso",
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "tonelada"
    assert data["simbolo"] == "t"
    assert data["tipo"] == "peso"
    assert "id" in data
    assert "created_at" in data


def test_crear_duplicado_simbolo(client, auth_headers):
    """POST / con símbolo duplicado devuelve 409"""
    client.post(BASE_URL, json={"nombre": "tonelada", "simbolo": "ton", "tipo": "peso"}, headers=auth_headers)
    response = client.post(BASE_URL, json={"nombre": "otra tonelada", "simbolo": "ton", "tipo": "peso"}, headers=auth_headers)
    assert response.status_code == 409


def test_obtener_por_id(client, auth_headers):
    """GET /{id} devuelve la unidad creada"""
    created = client.post(BASE_URL, json={
        "nombre": "centilitro", "simbolo": "cl", "tipo": "volumen",
    }, headers=auth_headers).json()
    response = client.get(f"{BASE_URL}{created['id']}")
    assert response.status_code == 200
    assert response.json()["simbolo"] == "cl"


def test_obtener_inexistente(client):
    """GET /{id} con id inexistente devuelve 404"""
    response = client.get(f"{BASE_URL}99999")
    assert response.status_code == 404


def test_actualizar_unidad(client, auth_headers):
    """PUT /{id} modifica los campos enviados"""
    created = client.post(BASE_URL, json={
        "nombre": "decilitro", "simbolo": "dl", "tipo": "volumen",
    }, headers=auth_headers).json()
    response = client.put(f"{BASE_URL}{created['id']}", json={"nombre": "decilitro actualizado"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["nombre"] == "decilitro actualizado"
    assert response.json()["simbolo"] == "dl"


def test_eliminar_unidad(client, auth_headers):
    """DELETE /{id} elimina la unidad (204), luego GET devuelve 404"""
    created = client.post(BASE_URL, json={
        "nombre": "microgramo", "simbolo": "ug", "tipo": "peso",
    }, headers=auth_headers).json()
    delete_resp = client.delete(f"{BASE_URL}{created['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204
    get_resp = client.get(f"{BASE_URL}{created['id']}")
    assert get_resp.status_code == 404


def test_crear_sin_auth(client):
    """POST / sin token devuelve 401"""
    response = client.post(BASE_URL, json={
        "nombre": "nanogramo", "simbolo": "ng", "tipo": "peso",
    })
    assert response.status_code == 401
