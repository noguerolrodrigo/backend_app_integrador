"""Tests del módulo ProductoIngrediente"""

BASE_URL = "/producto-ingrediente/"
PRODUCTOS_URL = "/api/v1/productos/"
INGREDIENTES_URL = "/ingredientes/"
UNIDADES_URL = "/api/v1/unidades-medida/"


def _crear_producto(client, headers, nombre="Pizza Test"):
    resp = client.post(PRODUCTOS_URL, json={
        "nombre": nombre,
        "descripcion": "Test",
        "precio_base": 1000,
        "imagenes_url": [],
        "stock_cantidad": 5,
        "disponible": True,
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _crear_ingrediente(client, headers, nombre="Queso Test"):
    resp = client.post(INGREDIENTES_URL, json={
        "nombre": nombre,
        "descripcion": "Test",
        "es_alergeno": False,
    }, headers=headers)
    assert resp.status_code == 201
    return resp.json()


def _get_unidad_id(client, simbolo="ud"):
    unidades = client.get(UNIDADES_URL).json()
    return next(u["id"] for u in unidades if u["simbolo"] == simbolo)


def test_crear_relacion_con_cantidad(client, auth_headers):
    """POST /producto-ingrediente/ con cantidad y unidad_medida_id debe crear la relación (201)"""
    producto = _crear_producto(client, auth_headers)
    ingrediente = _crear_ingrediente(client, auth_headers)
    unidad_id = _get_unidad_id(client, "g")

    response = client.post(BASE_URL, json={
        "producto_id": producto["id"],
        "ingrediente_id": ingrediente["id"],
        "es_removible": True,
        "cantidad": "2.500",
        "unidad_medida_id": unidad_id,
    })
    assert response.status_code == 201
    data = response.json()
    assert float(data["cantidad"]) == 2.5
    assert data["unidad_medida_id"] == unidad_id
    assert data["es_removible"] is True


def test_crear_relacion_cantidad_invalida(client, auth_headers):
    """POST con cantidad=0 debe devolver 422"""
    producto = _crear_producto(client, auth_headers, "Pizza Zero")
    ingrediente = _crear_ingrediente(client, auth_headers, "Sal Zero")
    unidad_id = _get_unidad_id(client, "g")

    response = client.post(BASE_URL, json={
        "producto_id": producto["id"],
        "ingrediente_id": ingrediente["id"],
        "es_removible": False,
        "cantidad": "0",
        "unidad_medida_id": unidad_id,
    })
    assert response.status_code == 422


def test_listar_relaciones_por_producto(client, auth_headers):
    """GET /producto-ingrediente/producto/{id} devuelve las relaciones del producto"""
    producto = _crear_producto(client, auth_headers, "Pizza Lista")
    ingrediente = _crear_ingrediente(client, auth_headers, "Tomate Lista")
    unidad_id = _get_unidad_id(client, "g")

    client.post(BASE_URL, json={
        "producto_id": producto["id"],
        "ingrediente_id": ingrediente["id"],
        "es_removible": False,
        "cantidad": "150.000",
        "unidad_medida_id": unidad_id,
    })
    response = client.get(f"{BASE_URL}producto/{producto['id']}")
    assert response.status_code == 200
    datos = response.json()
    assert len(datos) == 1
    assert datos[0]["ingrediente_id"] == ingrediente["id"]


def test_eliminar_relacion(client, auth_headers):
    """DELETE /producto-ingrediente/ debe eliminar la relación (204)"""
    producto = _crear_producto(client, auth_headers, "Pizza Delete")
    ingrediente = _crear_ingrediente(client, auth_headers, "Cebolla Delete")
    unidad_id = _get_unidad_id(client, "ud")

    client.post(BASE_URL, json={
        "producto_id": producto["id"],
        "ingrediente_id": ingrediente["id"],
        "es_removible": True,
        "cantidad": "1.000",
        "unidad_medida_id": unidad_id,
    })
    delete_resp = client.delete(
        BASE_URL,
        params={"producto_id": producto["id"], "ingrediente_id": ingrediente["id"]},
    )
    assert delete_resp.status_code == 204
