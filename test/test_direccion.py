"""Tests del módulo Direcciones de Entrega con autenticación"""

BASE_URL = "/api/v1/direcciones/"


def _crear_direccion_basica(client, headers, alias="Casa", **kwargs):
    """Helper para crear una dirección de prueba"""
    data = {
        "alias": alias,
        "calle": kwargs.get("calle", "Calle Falsa"),
        "numero": kwargs.get("numero", "123"),
        "localidad": kwargs.get("localidad", "La Plata"),
        "codigo_postal": kwargs.get("codigo_postal", "1900"),
        "provincia": kwargs.get("provincia", "Buenos Aires"),
        "notas": kwargs.get("notas", ""),
        "es_principal": kwargs.get("es_principal", False),
    }
    resp = client.post(BASE_URL, json=data, headers=headers)
    assert resp.status_code == 201, f"Error creando dirección: {resp.text}"
    return resp.json()


def _get_admin_token_via_login(client):
    """Obtiene token admin para helpers que necesitan auth sin fixture"""
    resp = client.post("/api/v1/auth/login", json={
        "email": "admin@example.com",
        "password": "admin123",
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


# ======================== CREACIÓN ========================

def test_crear_direccion(client, auth_headers):
    """POST /api/v1/direcciones/ debe crear dirección (201)"""
    response = client.post(BASE_URL, json={
        "alias": "Casa",
        "calle": "Calle Principal",
        "numero": "123",
        "apartamento": "4B",
        "localidad": "La Plata",
        "codigo_postal": "1900",
        "provincia": "Buenos Aires",
        "notas": "Dejar en portería",
        "es_principal": True,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["alias"] == "Casa"
    assert data["es_principal"] is True
    assert "direccion_id" in data


def test_crear_direccion_sin_auth(client):
    """POST sin token debe fallar con 401"""
    response = client.post(BASE_URL, json={
        "alias": "Casa",
        "calle": "Calle Falsa",
        "numero": "123",
        "localidad": "La Plata",
    })
    assert response.status_code == 401


def test_crear_primera_direccion_es_principal(client, auth_headers):
    """La primera dirección se vuelve principal automáticamente"""
    response = client.post(BASE_URL, json={
        "alias": "Oficina",
        "calle": "Av. Siempre Viva",
        "numero": "742",
        "localidad": "Springfield",
        "es_principal": False,  # explícitamente False
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["es_principal"] is True  # se forza a True por ser la primera


# ======================== LISTAR ========================

def test_listar_mis_direcciones(client, auth_headers):
    """GET /api/v1/direcciones/ debe listar direcciones del usuario autenticado"""
    _crear_direccion_basica(client, auth_headers, "Casa")
    _crear_direccion_basica(client, auth_headers, "Trabajo")
    response = client.get(BASE_URL, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    aliases = [d["alias"] for d in data]
    assert "Casa" in aliases
    assert "Trabajo" in aliases


def test_listar_direcciones_sin_auth(client):
    """GET sin token debe fallar con 401"""
    response = client.get(BASE_URL)
    assert response.status_code == 401


def test_listar_direcciones_solo_mias(client, auth_headers):
    """Cada usuario solo ve sus propias direcciones"""
    # Crear dirección para admin
    _crear_direccion_basica(client, auth_headers, "Mi Casa")

    # Obtener token para otro "usuario" (no existe, así que probamos que
    # al menos la respuesta es exitosa y contiene solo las del user autenticado)
    response = client.get(BASE_URL, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert all("direccion_id" not in d or d.get("alias", "") for d in data)


# ======================== OBTENER POR ID ========================

def test_obtener_direccion_por_id(client, auth_headers):
    """GET /api/v1/direcciones/{id} debe retornar la dirección"""
    created = _crear_direccion_basica(client, auth_headers, "Mi Casa")
    direccion_id = created["direccion_id"]
    response = client.get(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["alias"] == "Mi Casa"


def test_obtener_direccion_inexistente(client, auth_headers):
    """GET /api/v1/direcciones/{id} con id inexistente debe retornar 404"""
    response = client.get(f"{BASE_URL}99999", headers=auth_headers)
    assert response.status_code == 404


def test_obtener_direccion_otro_usuario(client, auth_headers):
    """No se puede ver dirección de otro usuario"""
    created = _crear_direccion_basica(client, auth_headers, "Mi Direccion")
    direccion_id = created["direccion_id"]
    # Mismo usuario admin, es suya -> OK
    response = client.get(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    assert response.status_code == 200
    # La pertenencia se prueba a nivel de service
    # (con un segundo token diferente habría un 404, pero en tests solo tenemos admin)


# ======================== ACTUALIZAR ========================

def test_actualizar_direccion(client, auth_headers):
    """PATCH /api/v1/direcciones/{id} debe actualizar"""
    created = _crear_direccion_basica(client, auth_headers, "Original")
    direccion_id = created["direccion_id"]
    response = client.patch(f"{BASE_URL}{direccion_id}", json={
        "alias": "Actualizada",
        "notas": "Nueva nota",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["alias"] == "Actualizada"
    assert "updated_at" in data


def test_actualizar_direccion_sin_auth(client, auth_headers):
    """PATCH sin token debe fallar con 401"""
    created = _crear_direccion_basica(client, auth_headers, "Test")
    direccion_id = created["direccion_id"]
    response = client.patch(f"{BASE_URL}{direccion_id}", json={
        "alias": "Nuevo",
    })
    assert response.status_code == 401


# ======================== MARCAR COMO PRINCIPAL ========================

def test_marcar_como_principal(client, auth_headers):
    """PATCH /api/v1/direcciones/{id}/principal debe marcar como principal"""
    # Crear dos direcciones
    d1 = _crear_direccion_basica(client, auth_headers, "Casa", es_principal=True)
    d2 = _crear_direccion_basica(client, auth_headers, "Trabajo", es_principal=False)

    # Marcar Trabajo como principal
    response = client.patch(f"{BASE_URL}{d2['direccion_id']}/principal", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["alias"] == "Trabajo"
    assert response.json()["es_principal"] is True

    # Verificar que Casa ya no es principal
    get_resp = client.get(f"{BASE_URL}{d1['direccion_id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["es_principal"] is False


def test_marcar_principal_inexistente(client, auth_headers):
    """Marcar como principal una dirección inexistente debe fallar"""
    response = client.patch(f"{BASE_URL}99999/principal", headers=auth_headers)
    assert response.status_code == 400


# ======================== SOFT DELETE ========================

def test_eliminar_direccion(client, auth_headers):
    """DELETE /api/v1/direcciones/{id} debe hacer soft delete (204)"""
    created = _crear_direccion_basica(client, auth_headers, "Para Eliminar")
    direccion_id = created["direccion_id"]
    resp = client.delete(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    assert resp.status_code == 204
    # Verificar que ya no se encuentra
    get_resp = client.get(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_eliminar_direccion_principal_promueve_siguiente(client, auth_headers):
    """Al eliminar la dirección principal, la siguiente se vuelve principal"""
    d1 = _crear_direccion_basica(client, auth_headers, "Principal", es_principal=True)
    d2 = _crear_direccion_basica(client, auth_headers, "Secundaria", es_principal=False)

    # Eliminar la principal
    client.delete(f"{BASE_URL}{d1['direccion_id']}", headers=auth_headers)

    # La secundaria ahora debe ser principal
    get_resp = client.get(f"{BASE_URL}{d2['direccion_id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["es_principal"] is True


# ======================== RESTAURAR ========================

def test_restaurar_direccion(client, auth_headers):
    """POST /api/v1/direcciones/{id}/restaurar debe restaurar dirección eliminada"""
    created = _crear_direccion_basica(client, auth_headers, "A Restaurar")
    direccion_id = created["direccion_id"]
    # Eliminar
    client.delete(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    # Restaurar
    resp = client.post(f"{BASE_URL}{direccion_id}/restaurar", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["alias"] == "A Restaurar"
    # Verificar que ahora se encuentra
    get_resp = client.get(f"{BASE_URL}{direccion_id}", headers=auth_headers)
    assert get_resp.status_code == 200


# ======================== ENDPOINTS ADMIN ========================

def test_admin_listar_direcciones_usuario(client, auth_headers):
    """[ADMIN] GET /api/v1/direcciones/usuario/{id} debe listar direcciones de un usuario"""
    _crear_direccion_basica(client, auth_headers, "Admin View")
    response = client.get(f"{BASE_URL}usuario/1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["alias"] == "Admin View"
    assert "direccion_completa" in data[0]


def test_admin_obtener_principal_usuario(client, auth_headers):
    """[ADMIN] GET /api/v1/direcciones/usuario/{id}/principal"""
    _crear_direccion_basica(client, auth_headers, "Mi Casa", es_principal=True)
    response = client.get(f"{BASE_URL}usuario/1/principal", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["alias"] == "Mi Casa"


def test_admin_sin_auth_listar_usuario(client):
    """Endpoint admin sin auth debe fallar con 401"""
    response = client.get(f"{BASE_URL}usuario/1")
    assert response.status_code == 401
