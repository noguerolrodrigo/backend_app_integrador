"""Tests del módulo Pedido — máquina de estados, snapshot pattern, cancelación"""

import pytest

API_PREFIX = "/api/v1/pedidos"
PRODUCTO_URL = "/api/v1/productos/"


# ===================== FIXTURES =====================

@pytest.fixture
def usuario_id(client):
    """Usa el usuario admin creado por seed (admin@example.com, ID 1)"""
    return 1


@pytest.fixture
def producto_id(client, auth_headers):
    """Crea un producto de prueba y retorna su ID"""
    resp = client.post(PRODUCTO_URL, json={
        "nombre": "Pizza Test",
        "descripcion": "Para pedidos",
        "precio_base": 1000,
        "imagenes_url": [],
        "stock_cantidad": 50,
        "disponible": True,
    }, headers=auth_headers)
    assert resp.status_code == 201, f"Error creando producto: {resp.text}"
    return resp.json()["id"]


@pytest.fixture
def producto_id_2(client, auth_headers):
    """Crea otro producto de prueba"""
    resp = client.post(PRODUCTO_URL, json={
        "nombre": "Empanada Test",
        "descripcion": "Para pedidos tambien",
        "precio_base": 500,
        "imagenes_url": [],
        "stock_cantidad": 30,
        "disponible": True,
    }, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


# ===================== HELPERS =====================

RESPONSE_HAS_PEDIDO_ID = True  # PedidoCreatedResponse usa pedido_id, no id


def _crear_pedido_base(client, usuario_id, producto_id):
    """Helper para crear un pedido basico y retornar su ID"""
    resp = client.post(f"{API_PREFIX}/", json={
        "usuario_id": usuario_id,
        "forma_pago": "EFECTIVO",
        "direccion_entrega": "Calle Test 123",
        "detalles": [{"producto_id": producto_id, "cantidad": 1}],
    })
    assert resp.status_code == 201, f"Error creando pedido: {resp.text}"
    data = resp.json()
    # La respuesta usa pedido_id (PedidoCreatedResponse)
    return data["pedido_id"]


# ===================== CREACION DE PEDIDOS =====================

def test_crear_pedido_exitoso(client, usuario_id, producto_id):
    """POST /api/v1/pedidos/ debe crear un pedido correctamente"""
    response = client.post(f"{API_PREFIX}/", json={
        "usuario_id": usuario_id,
        "forma_pago": "TARJETA_CREDITO",
        "direccion_entrega": "Calle Principal 123",
        "observaciones": "Dejar en porteria",
        "detalles": [
            {"producto_id": producto_id, "cantidad": 2},
        ],
    })
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "PENDIENTE"
    assert data["monto_total"] == 2000  # 1000 * 2
    assert "pedido_id" in data
    assert "numero_pedido" in data


def test_crear_pedido_con_producto_inexistente(client, usuario_id):
    """Crear pedido con producto que no existe debe fallar"""
    response = client.post(f"{API_PREFIX}/", json={
        "usuario_id": usuario_id,
        "forma_pago": "EFECTIVO",
        "direccion_entrega": "Calle 5",
        "detalles": [
            {"producto_id": 99999, "cantidad": 1},
        ],
    })
    assert response.status_code in (400, 404)


def test_crear_pedido_sin_stock(client, usuario_id, producto_id):
    """Crear pedido con cantidad mayor al stock disponible debe fallar"""
    response = client.post(f"{API_PREFIX}/", json={
        "usuario_id": usuario_id,
        "forma_pago": "MERCADO_PAGO",
        "direccion_entrega": "Calle 10",
        "detalles": [
            {"producto_id": producto_id, "cantidad": 99999},
        ],
    })
    assert response.status_code == 400


# ===================== LISTAR PEDIDOS =====================

def test_listar_pedidos_con_paginacion(client, auth_headers, usuario_id, producto_id, producto_id_2):
    """GET /api/v1/pedidos/?skip=0&limit=10 debe paginar"""
    _crear_pedido_base(client, usuario_id, producto_id)
    _crear_pedido_base(client, usuario_id, producto_id_2)
    response = client.get(f"{API_PREFIX}/?skip=0&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2, f"Esperados >=2 pedidos, obtenidos {len(data)}"


def test_listar_pedidos_por_usuario(client, auth_headers, usuario_id, producto_id):
    """GET /api/v1/pedidos/usuario/{id} debe filtrar por usuario"""
    _crear_pedido_base(client, usuario_id, producto_id)
    response = client.get(f"{API_PREFIX}/usuario/{usuario_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1


# ===================== MAQUINA DE ESTADOS =====================

def test_flujo_completo_estados(client, auth_headers, usuario_id, producto_id):
    """Flujo completo: PENDIENTE > CONFIRMADO > EN_PREPARACION > EN_CAMINO > ENTREGADO"""
    pedido_id = _crear_pedido_base(client, usuario_id, producto_id)

    transiciones = [
        ("CONFIRMADO", "Cliente confirmo"),
        ("EN_PREPARACION", "Cocina inicio"),
        ("EN_CAMINO", "En ruta"),
        ("ENTREGADO", "Entregado"),
    ]

    for estado_nuevo, razon in transiciones:
        resp = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
            "estado_nuevo": estado_nuevo,
            "razon": razon,
        }, headers=auth_headers)
        assert resp.status_code == 200, f"Fallo en transicion a {estado_nuevo}: {resp.text}"
        assert resp.json()["estado_nuevo"] == estado_nuevo

    # Verificar historial append-only con 5 registros (creacion + 4 transiciones)
    historial = client.get(f"{API_PREFIX}/{pedido_id}/historial", headers=auth_headers)
    assert historial.status_code == 200
    registros = historial.json()
    assert len(registros) == 5, f"Esperados 5 registros, obtenidos {len(registros)}"


def test_transicion_invalida(client, auth_headers, usuario_id, producto_id):
    """Transicion de ENTREGADO a PENDIENTE debe fallar"""
    pedido_id = _crear_pedido_base(client, usuario_id, producto_id)

    for estado in ["CONFIRMADO", "EN_PREPARACION", "EN_CAMINO", "ENTREGADO"]:
        resp = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
            "estado_nuevo": estado,
            "razon": f"Avanzando a {estado}",
        }, headers=auth_headers)
        assert resp.status_code == 200, f"Fallo avanzando a {estado}: {resp.text}"

    # Intentar volver a PENDIENTE (debe fallar por maquina de estados)
    resp = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
        "estado_nuevo": "PENDIENTE",
        "razon": "Intento invalido",
    }, headers=auth_headers)
    assert resp.status_code == 400


# ===================== CANCELACION =====================

def test_cancelar_pedido_pendiente(client, auth_headers, usuario_id, producto_id):
    """Cancelar pedido en PENDIENTE debe funcionar"""
    pedido_id = _crear_pedido_base(client, usuario_id, producto_id)
    resp = client.post(f"{API_PREFIX}/{pedido_id}/cancelar?razon=Cambio+de+opinion", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["estado_nuevo"] == "CANCELADO"


def test_no_cancelar_pedido_en_preparacion(client, auth_headers, usuario_id, producto_id):
    """Cancelar pedido en EN_PREPARACION debe fallar"""
    pedido_id = _crear_pedido_base(client, usuario_id, producto_id)

    # Transicion valida: PENDIENTE > CONFIRMADO > EN_PREPARACION
    resp1 = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
        "estado_nuevo": "CONFIRMADO", "razon": "Confirmado",
    }, headers=auth_headers)
    assert resp1.status_code == 200, f"Fallo CONFIRMADO: {resp1.text}"

    resp2 = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
        "estado_nuevo": "EN_PREPARACION", "razon": "Cocina inicio",
    }, headers=auth_headers)
    assert resp2.status_code == 200, f"Fallo EN_PREPARACION: {resp2.text}"

    # Ahora debe fallar la cancelacion
    resp = client.post(f"{API_PREFIX}/{pedido_id}/cancelar?razon=Cambio+de+idea", headers=auth_headers)
    assert resp.status_code == 400


# ===================== SNAPSHOT PATTERN =====================

def test_snapshot_pattern_precio_inmutable(client, usuario_id, auth_headers):
    """El precio del producto se congela al crear el pedido (snapshot)"""
    # Crear producto
    prod_resp = client.post(PRODUCTO_URL, json={
        "nombre": "Producto Snapshot",
        "descripcion": "Para probar snapshot",
        "precio_base": 1000,
        "imagenes_url": [],
        "stock_cantidad": 10,
        "disponible": True,
    }, headers=auth_headers)
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["id"]

    # Crear pedido con precio 1000
    pedido_resp = client.post(f"{API_PREFIX}/", json={
        "usuario_id": usuario_id,
        "forma_pago": "EFECTIVO",
        "direccion_entrega": "Snapshot Test",
        "detalles": [{"producto_id": prod_id, "cantidad": 1}],
    })
    assert pedido_resp.status_code == 201
    pedido_id = pedido_resp.json()["pedido_id"]

    # Actualizar precio del producto a 9999
    client.put(f"{PRODUCTO_URL}{prod_id}", json={
        "nombre": "Producto Snapshot",
        "descripcion": "Para probar snapshot",
        "precio_base": 9999,
        "imagenes_url": [],
        "stock_cantidad": 10,
        "disponible": True,
    }, headers=auth_headers)

    # El pedido debe mantener el precio original (snapshot)
    # GET /{id} requiere get_current_user (usar auth_headers del admin para acceder)
    pedido_resp = client.get(f"{API_PREFIX}/{pedido_id}", headers=auth_headers)
    assert pedido_resp.status_code == 200
    detalle = pedido_resp.json()["detalles"][0]
    assert detalle["precio_unitario"] == 1000, (
        f"Esperado 1000 (snapshot), obtenido {detalle['precio_unitario']}"
    )
    assert detalle["subtotal"] == 1000


# ===================== VERIFICAR CANCELACION =====================

def test_puede_cancelarse_endpoint(client, auth_headers, usuario_id, producto_id):
    """GET /api/v1/pedidos/{id}/puede-cancelarse"""
    pedido_id = _crear_pedido_base(client, usuario_id, producto_id)

    # Pendiente -> debe poder cancelarse
    resp = client.get(f"{API_PREFIX}/{pedido_id}/puede-cancelarse", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["puede_cancelarse"] is True

    # Avanzar a CONFIRMADO -> aun puede cancelarse
    resp_confirmado = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
        "estado_nuevo": "CONFIRMADO",
        "razon": "Confirmado",
    }, headers=auth_headers)
    assert resp_confirmado.status_code == 200

    resp = client.get(f"{API_PREFIX}/{pedido_id}/puede-cancelarse", headers=auth_headers)
    assert resp.status_code == 200
    # Confirmado aun puede cancelarse
    assert resp.json()["puede_cancelarse"] is True
    assert resp.json()["estado_actual"] == "CONFIRMADO"

    # Avanzar a EN_PREPARACION -> ya no puede cancelarse
    resp_prep = client.patch(f"{API_PREFIX}/{pedido_id}/estado", json={
        "estado_nuevo": "EN_PREPARACION",
        "razon": "Cocina inicio",
    }, headers=auth_headers)
    assert resp_prep.status_code == 200

    resp = client.get(f"{API_PREFIX}/{pedido_id}/puede-cancelarse", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["puede_cancelarse"] is False
    assert resp.json()["estado_actual"] == "EN_PREPARACION"
