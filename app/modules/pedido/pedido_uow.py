"""Unit of Work contextual para el módulo de Pedido."""

from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.pedido.repository import (
    PedidoRepository,
    DetallePedidoRepository,
    HistorialEstadoPedidoRepository,
)


class PedidoUnitOfWork:
    """Unit of Work del módulo Pedido.

    Encapsula una transacción completa con sesión propia y los repos
    específicos del módulo (pedido, detalle, historial_estado).
    """

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session
        self.pedidos: Optional[PedidoRepository] = None
        self.detalles: Optional[DetallePedidoRepository] = None
        self.historial: Optional[HistorialEstadoPedidoRepository] = None

    def _initialize_repos(self) -> None:
        self.pedidos = PedidoRepository(self.session)
        self.detalles = DetallePedidoRepository(self.session)
        self.historial = HistorialEstadoPedidoRepository(self.session)

    def __enter__(self) -> "PedidoUnitOfWork":
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
        self._initialize_repos()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: object,
    ) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            if not self._external_session:
                self.session.close()
