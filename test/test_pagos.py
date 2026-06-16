"""Tests del módulo Pagos — MP SDK mockeado"""
from unittest.mock import MagicMock, patch

PAGOS_URL = "/api/v1/pagos/"
PEDIDOS_URL = "/api/v1/pedidos/"
PRODUCTOS_URL = "/api/v1/productos/"


def _mp_response(status="approved", payment_id=12345):
    return {
        "status": 201,
        "response": {
            "id": payment_id,
            "status": status,
            "status_detail": "accredited" if status == "approved" else "pending_contingency",
            "transaction_amount": 100.0,
            "payment_method_id": "visa",
            "external_reference": "1",
        },
    }


def _crear_producto(client, headers):
    r = client.post(PRODUCTOS_URL, json={
        "nombre": "Test Pago",
        "descripcion": "Producto para test de pagos",
        "precio_base": 100,
        "imagenes_url": [],
        "stock_cantidad": 10,
        "disponible": True,
    }, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def _crear_pedido(client, producto_id):
    r = client.post(PEDIDOS_URL, json={
        "usuario_id": 1,
        "forma_pago": "MERCADO_PAGO",
        "direccion_entrega": "Calle Test 123",
        "detalles": [{"producto_id": producto_id, "cantidad": 1}],
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_crear_pago_approved(client, auth_headers):
    """POST /crear con pago aprobado → 201, mp_status=approved"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    mock_sdk = MagicMock()
    mock_sdk.payment.return_value.create.return_value = _mp_response("approved", 11111)

    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_sdk):
        resp = client.post(f"{PAGOS_URL}crear", json={
            "pedido_id": pedido_id,
            "token": "test-card-token",
            "installments": 1,
            "payment_method_id": "visa",
        }, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["mp_status"] == "approved"
    assert data["pedido_id"] == pedido_id
    assert data["mp_payment_id"] == 11111
    assert "idempotency_key" in data


def test_crear_pago_pending(client, auth_headers):
    """POST /crear con pago pendiente → 201, mp_status=pending, pedido no cambia estado"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    mock_sdk = MagicMock()
    mock_sdk.payment.return_value.create.return_value = _mp_response("pending", 22222)

    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_sdk):
        resp = client.post(f"{PAGOS_URL}crear", json={
            "pedido_id": pedido_id,
            "token": "test-token",
            "installments": 1,
            "payment_method_id": "master",
        }, headers=auth_headers)

    assert resp.status_code == 201, resp.text
    assert resp.json()["mp_status"] == "pending"

    # Pedido debe seguir PENDIENTE — verificar via lista (evita el lazy-load de detalles)
    lista = client.get(PEDIDOS_URL, headers=auth_headers).json()
    mi_pedido = next(p for p in lista if p["id"] == pedido_id)
    assert mi_pedido["estado"] == "PENDIENTE"


def test_webhook_approved_confirma_pedido(client, auth_headers):
    """POST /webhook con payment approved → pedido pasa a CONFIRMADO"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    # Primero crear el pago en pending
    mock_create = MagicMock()
    mock_create.payment.return_value.create.return_value = _mp_response("pending", 77777)
    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_create):
        client.post(f"{PAGOS_URL}crear", json={
            "pedido_id": pedido_id,
            "token": "tok",
            "installments": 1,
            "payment_method_id": "visa",
        }, headers=auth_headers)

    # Webhook MP notifica pago aprobado
    mock_get = MagicMock()
    mock_get.payment.return_value.get.return_value = {
        "status": 200,
        "response": {
            "id": 77777,
            "status": "approved",
            "status_detail": "accredited",
            "transaction_amount": 100.0,
            "payment_method_id": "visa",
            "external_reference": str(pedido_id),
        },
    }
    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_get):
        resp = client.post(f"{PAGOS_URL}webhook", json={
            "type": "payment",
            "data": {"id": "77777"},
        })

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    # Pedido ahora debe estar CONFIRMADO — verificar via lista (evita lazy-load de detalles)
    lista = client.get(PEDIDOS_URL, headers=auth_headers).json()
    mi_pedido = next(p for p in lista if p["id"] == pedido_id)
    assert mi_pedido["estado"] == "CONFIRMADO"


def test_obtener_pago(client, auth_headers):
    """GET /{pedido_id} devuelve el pago asociado al pedido"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    mock_sdk = MagicMock()
    mock_sdk.payment.return_value.create.return_value = _mp_response("approved", 33333)
    with patch("app.modules.pagos.service.get_mp_sdk", return_value=mock_sdk):
        client.post(f"{PAGOS_URL}crear", json={
            "pedido_id": pedido_id,
            "token": "tok",
            "installments": 1,
            "payment_method_id": "visa",
        }, headers=auth_headers)

    resp = client.get(f"{PAGOS_URL}{pedido_id}", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["pedido_id"] == pedido_id
    assert data["mp_status"] == "approved"


def test_webhook_tipo_no_payment_ignorado(client):
    """POST /webhook con type != payment → 200 sin procesar nada"""
    resp = client.post(f"{PAGOS_URL}webhook", json={
        "type": "merchant_order",
        "data": {"id": "555"},
    })
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
