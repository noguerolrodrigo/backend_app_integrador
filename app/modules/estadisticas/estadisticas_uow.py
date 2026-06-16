from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.estadisticas.repository import EstadisticasRepository


class EstadisticasUnitOfWork:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session

    def __enter__(self) -> "EstadisticasUnitOfWork":
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
        self.repo = EstadisticasRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        # Read-only: sin commit
        if not self._external_session:
            self.session.close()
