"""Unit of Work contextual para el módulo de Dirección."""

from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.direccion.repository import DireccionEntregaRepository


class DireccionUnitOfWork:
    """Unit of Work del módulo Dirección.

    Encapsula una transacción completa con sesión propia y el repo
    específico del módulo (direccion_entrega).
    """

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session
        self.direcciones: Optional[DireccionEntregaRepository] = None

    def _initialize_repos(self) -> None:
        self.direcciones = DireccionEntregaRepository(self.session)

    def __enter__(self) -> "DireccionUnitOfWork":
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
