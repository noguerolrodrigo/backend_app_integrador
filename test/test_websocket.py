"""Tests del endpoint WebSocket /ws/pedidos"""
import pytest

PEDIDOS_URL = "/api/v1/pedidos/"
PRODUCTOS_URL = "/api/v1/productos/"
WS_URL = "/ws/pedidos"


def _crear_producto(client, headers):
    r = client.post(PRODUCTOS_URL, json={
        "nombre": "Test WS",
        "descripcion": "Producto para test WS",
        "precio_base": 100,
        "imagenes_url": [],
        "stock_cantidad": 99,
        "disponible": True,
    }, headers=headers)
    assert r.status_code == 201
    return r.json()


def _crear_pedido(client, producto_id):
    r = client.post(PEDIDOS_URL, json={
        "usuario_id": 1,
        "forma_pago": "EFECTIVO",
        "direccion_entrega": "Calle Falsa 123",
        "detalles": [{"producto_id": producto_id, "cantidad": 1}],
    })
    assert r.status_code == 201
    return r.json()


def test_ws_sin_token_cierra_conexion(client):
    """Conectar sin token debe cerrar la conexión con error"""
    with pytest.raises(Exception):
        with client.websocket_connect(WS_URL) as ws:
            ws.receive_json()


def test_ws_token_invalido_cierra_conexion(client):
    """Conectar con token inválido debe cerrar la conexión con error"""
    with pytest.raises(Exception):
        with client.websocket_connect(f"{WS_URL}?token=invalido") as ws:
            ws.receive_json()


def test_ws_conexion_exitosa(client, admin_token):
    """Token ADMIN válido debe permitir conectarse sin error"""
    with client.websocket_connect(f"{WS_URL}?token={admin_token}") as ws:
        pass  # Conexión establecida sin excepción


def test_ws_recibe_evento_cambio_estado(client, auth_headers, admin_token):
    """Al avanzar estado de un pedido, el cliente WS debe recibir el evento estado_cambiado"""
    producto = _crear_producto(client, auth_headers)
    pedido = _crear_pedido(client, producto["id"])
    pedido_id = pedido["pedido_id"]

    with client.websocket_connect(f"{WS_URL}?token={admin_token}") as ws:
        client.patch(
            f"{PEDIDOS_URL}{pedido_id}/estado",
            json={"estado_nuevo": "CONFIRMADO", "razon": "Test WebSocket"},
            headers=auth_headers,
        )
        evento = ws.receive_json()
        assert evento["event"] == "estado_cambiado"
        assert evento["pedido_id"] == pedido_id
        assert evento["estado_nuevo"] == "CONFIRMADO"
        assert evento["estado_anterior"] == "PENDIENTE"
        assert "timestamp" in evento
        assert "usuario_id" in evento
