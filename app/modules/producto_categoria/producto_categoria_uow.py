"""Unit of Work contextual para el módulo de Producto-Categoría."""

from typing import Optional

from sqlmodel import Session

from app.core.database import engine


class ProductoCategoriaUnitOfWork:
    """Unit of Work del módulo Producto-Categoría.

    Encapsula una transacción con sesión propia.
    No tiene repositorios específicos (usa session directa).
    """

    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session

    def __enter__(self) -> "ProductoCategoriaUnitOfWork":
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
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
