from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.database import engine
from app.core.security import decode_access_token
from app.core.ws_manager import ws_manager
from app.modules.usuario.models import Usuario

ws_router = APIRouter()


@ws_router.websocket("/ws/pedidos")
async def ws_pedidos(ws: WebSocket, token: str | None = Query(default=None)):
    await ws.accept()

    if not token:
        await ws.close(code=4001, reason="Token requerido")
        return

    payload = decode_access_token(token)
    if not payload:
        await ws.close(code=4001, reason="Token inválido o expirado")
        return

    user_id = payload.get("user_id")
    with Session(engine) as session:
        usuario = session.exec(
            select(Usuario)
            .where(Usuario.id == int(user_id), Usuario.deleted_at.is_(None))
            .options(selectinload(Usuario.roles))
        ).first()

    if not usuario or not usuario.is_active():
        await ws.close(code=4001, reason="Usuario inválido")
        return

    if not {r.codigo for r in usuario.roles} & {"ADMIN", "PEDIDOS"}:
        await ws.close(code=4003, reason="Sin permisos")
        return

    # ws ya está aceptado — agregar directo al pool (no llamar connect() que haría accept() de nuevo)
    ws_manager._connections["admin"].add(ws)
    try:
        while True:
            await ws.receive_text()  # mantiene vivo el socket; mensajes del cliente se ignoran
    except WebSocketDisconnect:
        pass
    finally:
        ws_manager.disconnect(ws, "admin")
