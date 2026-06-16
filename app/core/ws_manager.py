from collections import defaultdict

from fastapi import WebSocket


class WSManager:
    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, ws: WebSocket, canal: str) -> None:
        await ws.accept()
        self._connections[canal].add(ws)

    def disconnect(self, ws: WebSocket, canal: str) -> None:
        self._connections[canal].discard(ws)

    async def broadcast_pedido(self, pedido_id: int, evento: dict) -> None:
        for canal in (str(pedido_id), "admin"):
            await self._send_to_canal(canal, evento)

    async def broadcast_to_role(self, rol: str, evento: dict) -> None:
        await self._send_to_canal(rol, evento)

    async def _send_to_canal(self, canal: str, evento: dict) -> None:
        muertos: set[WebSocket] = set()
        for ws in list(self._connections.get(canal, [])):
            try:
                await ws.send_json(evento)
            except Exception:
                muertos.add(ws)
        for ws in muertos:
            self._connections[canal].discard(ws)


ws_manager = WSManager()
