"""Tests CRUD del módulo Producto"""

BASE_URL = "/api/v1/productos/"
UNIDADES_URL = "/api/v1/unidades-medida/"
INGREDIENTES_URL = "/ingredientes/"
PI_URL = "/producto-ingrediente/"


def _crear_producto_basico(client, nombre="Pizza Clásica", precio=1200, headers=None):
    """Helper para crear un producto"""
    hdrs = headers or {}
    resp = client.post(BASE_URL, json={
        "nombre": nombre,
        "descripcion": "Producto de prueba",
        "precio_base": precio,
        "imagenes_url": [],
        "stock_cantidad": 10,
        "disponible": True,
    }, headers=hdrs)
    assert resp.status_code == 201
    return resp.json()


def _get_unidad_id(client, simbolo="ud"):
    """Helper: obtiene el id de una unidad de medida por símbolo (del seed)"""
    unidades = client.get(UNIDADES_URL).json()
    return next(u["id"] for u in unidades if u["simbolo"] == simbolo)


def test_crear_producto(client, auth_headers):
    """POST /api/v1/productos/ debe crear un producto (201)"""
    response = client.post(BASE_URL, json={
        "nombre": "Pizza Pepperoni",
        "descripcion": "Con pepperoni y queso",
        "precio_base": 1500,
        "imagenes_url": [],
        "stock_cantidad": 20,
        "disponible": True,
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Pizza Pepperoni"
    assert data["precio_base"] == 1500
    assert data["stock_cantidad"] == 20
    assert data["disponible"] is True


def test_listar_productos(client, auth_headers):
    """GET /api/v1/productos/ debe listar productos"""
    _crear_producto_basico(client, "Pizza 1", headers=auth_headers)
    _crear_producto_basico(client, "Pizza 2", headers=auth_headers)
    response = client.get(BASE_URL)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_obtener_producto_por_id(client, auth_headers):
    """GET /api/v1/productos/{id} debe retornar un producto"""
    created = _crear_producto_basico(client, "Pizza ID Test", headers=auth_headers)
    response = client.get(f"{BASE_URL}{created['id']}")
    assert response.status_code == 200
    assert response.json()["nombre"] == "Pizza ID Test"


def test_obtener_producto_inexistente(client):
    """GET /api/v1/productos/{id} inexistente debe retornar 404"""
    response = client.get(f"{BASE_URL}99999")
    assert response.status_code == 404


def test_filtrar_productos_por_precio(client, auth_headers):
    """GET /api/v1/productos?min_precio=&max_precio= debe filtrar"""
    _crear_producto_basico(client, "Económico", precio=500, headers=auth_headers)
    _crear_producto_basico(client, "Premium", precio=2000, headers=auth_headers)
    response = client.get(f"{BASE_URL}?min_precio=1000&max_precio=2500")
    assert response.status_code == 200
    data = response.json()
    assert all(p["precio_base"] >= 1000 for p in data)
    assert all(p["precio_base"] <= 2500 for p in data)


def test_actualizar_producto(client, auth_headers):
    """PUT /api/v1/productos/{id} debe actualizar"""
    created = _crear_producto_basico(client, "Original", headers=auth_headers)
    response = client.put(f"{BASE_URL}{created['id']}", json={
        "nombre": "Actualizado",
        "descripcion": "Nueva descripción",
        "precio_base": 2000,
        "imagenes_url": [],
        "stock_cantidad": 5,
        "disponible": True,
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["nombre"] == "Actualizado"
    assert response.json()["precio_base"] == 2000


def test_eliminar_producto(client, auth_headers):
    """DELETE /api/v1/productos/{id} debe eliminar (204)"""
    created = _crear_producto_basico(client, "Para Eliminar", headers=auth_headers)
    delete_resp = client.delete(f"{BASE_URL}{created['id']}", headers=auth_headers)
    assert delete_resp.status_code == 204
    get_resp = client.get(f"{BASE_URL}{created['id']}")
    assert get_resp.status_code == 404


def test_crear_producto_con_unidad_venta(client, auth_headers):
    """POST con unidad_venta_id válido (del seed) debe crear el producto con esa FK"""
    unidad_id = _get_unidad_id(client, "ud")
    response = client.post(BASE_URL, json={
        "nombre": "Empanada",
        "descripcion": "Rellena",
        "precio_base": 350,
        "imagenes_url": [],
        "stock_cantidad": 50,
        "disponible": True,
        "unidad_venta_id": unidad_id,
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json()["unidad_venta_id"] == unidad_id


def test_actualizar_imagenes(client, auth_headers):
    """PATCH /{id}/imagenes debe reemplazar el array de imágenes"""
    created = _crear_producto_basico(client, "Con Imagenes", headers=auth_headers)
    nuevas = ["https://example.com/a.jpg", "https://example.com/b.jpg"]
    response = client.patch(
        f"{BASE_URL}{created['id']}/imagenes",
        json={"imagenes_url": nuevas},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["imagenes_url"] == nuevas


def test_listar_ingredientes_de_producto(client, auth_headers):
    """GET /{id}/ingredientes devuelve la lista de ingredientes asociados"""
    producto = _crear_producto_basico(client, "Pizza Margherita", headers=auth_headers)
    ingrediente = client.post(INGREDIENTES_URL, json={
        "nombre": "Queso", "descripcion": "Mozzarella", "es_alergeno": False,
    }, headers=auth_headers).json()
    unidad_id = _get_unidad_id(client, "g")
    client.post(PI_URL, json={
        "producto_id": producto["id"],
        "ingrediente_id": ingrediente["id"],
        "es_removible": True,
        "cantidad": "100.000",
        "unidad_medida_id": unidad_id,
    })
    response = client.get(f"{BASE_URL}{producto['id']}/ingredientes")
    assert response.status_code == 200
    ids = [i["id"] for i in response.json()]
    assert ingrediente["id"] in ids
