"""Tests del módulo Estadísticas — solo lectura, exclusivo ADMIN"""
from datetime import date
from unittest.mock import MagicMock, patch

BASE_URL = "/api/v1/estadisticas"
PEDIDOS_URL = "/api/v1/pedidos/"
PRODUCTOS_URL = "/api/v1/productos/"
PAGOS_URL = "/api/v1/pagos/"


# ─── helpers ──────────────────────────────────────────────────────────────────

def _crear_producto(client, headers):
    r = client.post(PRODUCTOS_URL, json={
        "nombre": "Producto Stats",
        "descripcion": "Para tests de estadísticas",
        "precio_base": 200,
        "imagenes_url": [],
        "stock_cantidad": 50,
        "disponible": True,
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _crear_pedido(client, producto_id, forma_pago="EFECTIVO"):
    r = client.post(PEDIDOS_URL, json={
        "usuario_id": 1,
        "forma_pago": forma_pago,
        "direccion_entrega": "Calle Stats 123",
        "detalles": [{"producto_id": producto_id, "cantidad": 2}],
    })
    assert r.status_code == 201, r.text
    return r.json()


def _mp_response(status="approved", payment_id=99001):
    return {
        "status": 201,
        "response": {
            "id": payment_id,
            "status": status,
            "status_detail": "accredited" if status == "approved" else "pending_contingency",
            "transaction_amount": 400.0,
            "payment_method_id": "visa",
            "external_reference": "1",
        },
    }


def _crear_pago(client, pedido_id, headers, mp_status="approved", payment_id=99001):
    mock_sdk = MagicMock()
    mock_sdk.payment.return_value.create.return_value = _mp_response(mp_status, payment_id)
    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_sdk):
        r = client.post(f"{PAGOS_URL}crear", json={
            "pedido_id": pedido_id,
            "token": "test-token",
            "installments": 1,
            "payment_method_id": "visa",
        }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _today_str():
    from datetime import datetime
    return datetime.utcnow().date().isoformat()


# ─── tests ────────────────────────────────────────────────────────────────────

def test_estadisticas_requiere_admin(client):
    """Sin autenticación → 401 en todos los endpoints"""
    r = client.get(f"{BASE_URL}/resumen")
    assert r.status_code == 401


def test_resumen_estructura(client, auth_headers):
    """GET /resumen devuelve los 4 KPIs con tipos correctos"""
    r = client.get(f"{BASE_URL}/resumen", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "ventas_hoy" in data
    assert "ticket_promedio" in data
    assert "pedidos_activos" in data
    assert "ventas_mes_actual" in data
    # Deben ser numéricos (string representación de Decimal)
    float(data["ventas_hoy"])
    float(data["ticket_promedio"])
    assert isinstance(data["pedidos_activos"], int)


def test_resumen_cuenta_pedidos_activos(client, auth_headers):
    """Pedidos no terminales incrementan pedidos_activos"""
    producto = _crear_producto(client, auth_headers)
    _crear_pedido(client, producto["id"])

    r = client.get(f"{BASE_URL}/resumen", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["pedidos_activos"] >= 1


def test_resumen_excluye_cancelado(client, auth_headers):
    """Pedido CANCELADO no suma a pedidos_activos ni a ventas_hoy"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    # Cancelar el pedido
    client.post(f"{PEDIDOS_URL}{pedido_id}/cancelar", headers=auth_headers)

    r = client.get(f"{BASE_URL}/resumen", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    # El pedido cancelado no debe aparecer como activo
    assert data["pedidos_activos"] == 0
    # ventas_hoy debe ser 0 (el pedido cancelado se excluye)
    assert float(data["ventas_hoy"]) == 0.0


def test_ventas_periodo_retorna_lista(client, auth_headers):
    """GET /ventas con rango de fechas retorna lista con estructura correcta"""
    producto = _crear_producto(client, auth_headers)
    _crear_pedido(client, producto["id"])

    hoy = _today_str()
    r = client.get(
        f"{BASE_URL}/ventas",
        params={"desde": hoy, "hasta": hoy, "agrupacion": "day"},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    if data:
        item = data[0]
        assert "periodo" in item
        assert "total_ventas" in item
        assert "cantidad_pedidos" in item
        assert item["cantidad_pedidos"] >= 1


def test_ventas_agrupacion_invalida(client, auth_headers):
    """agrupacion con valor no permitido → 400"""
    hoy = _today_str()
    r = client.get(
        f"{BASE_URL}/ventas",
        params={"desde": hoy, "hasta": hoy, "agrupacion": "quarter"},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_ventas_excluye_cancelado(client, auth_headers):
    """Pedido CANCELADO no aparece en ventas del período"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    client.post(f"{PEDIDOS_URL}{pedido_id}/cancelar", headers=auth_headers)

    hoy = _today_str()
    r = client.get(
        f"{BASE_URL}/ventas",
        params={"desde": hoy, "hasta": hoy, "agrupacion": "day"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    # Con solo el pedido cancelado, la lista debe estar vacía
    assert data == []


def test_productos_top_retorna_lista(client, auth_headers):
    """GET /productos-top con pedido activo devuelve al menos un producto"""
    producto = _crear_producto(client, auth_headers)
    _crear_pedido(client, producto["id"])

    r = client.get(f"{BASE_URL}/productos-top", params={"limit": 5}, headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "producto_id" in item
    assert "nombre" in item
    assert "total_ingresos" in item
    assert "cantidad_vendida" in item


def test_productos_top_excluye_cancelado(client, auth_headers):
    """Producto de pedido CANCELADO no aparece en el top"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    client.post(f"{PEDIDOS_URL}{pedido_id}/cancelar", headers=auth_headers)

    r = client.get(f"{BASE_URL}/productos-top", headers=auth_headers)
    assert r.status_code == 200
    # Con solo el pedido cancelado, no hay productos top
    assert r.json() == []


def test_pedidos_por_estado_retorna_lista(client, auth_headers):
    """GET /pedidos-por-estado devuelve lista con estado y cantidad"""
    producto = _crear_producto(client, auth_headers)
    _crear_pedido(client, producto["id"])

    r = client.get(f"{BASE_URL}/pedidos-por-estado", headers=auth_headers)
    assert r.status_code == 200, r.text
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    item = data[0]
    assert "estado" in item
    assert "cantidad" in item
    assert item["cantidad"] >= 1


def test_ingresos_solo_approved(client, auth_headers):
    """GET /ingresos cuenta solo pagos mp_status=approved; pending no aparece"""
    producto = _crear_producto(client, auth_headers)

    # Pedido con pago PENDING — no debe aparecer en ingresos
    pedido_pending = _crear_pedido(client, producto["id"], "MERCADO_PAGO")
    _crear_pago(client, pedido_pending["pedido_id"], auth_headers, "pending", 88001)

    hoy = _today_str()
    r = client.get(
        f"{BASE_URL}/ingresos",
        params={"desde": hoy, "hasta": hoy},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    # Pago pending → no aparece en ingresos
    assert data["items"] == []


def test_ingresos_approved_aparece(client, auth_headers):
    """GET /ingresos muestra pago approved con forma_pago y total correctos"""
    producto = _crear_producto(client, auth_headers)

    pedido = _crear_pedido(client, producto["id"], "MERCADO_PAGO")
    _crear_pago(client, pedido["pedido_id"], auth_headers, "approved", 88002)

    hoy = _today_str()
    r = client.get(
        f"{BASE_URL}/ingresos",
        params={"desde": hoy, "hasta": hoy},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["forma_pago"] == "MERCADO_PAGO"
    assert item["cantidad_pagos"] == 1
    assert float(item["total"]) > 0
