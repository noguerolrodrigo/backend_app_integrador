from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.pagos.repository import PagoRepository


class PagoUnitOfWork:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session
        self.pagos: Optional[PagoRepository] = None

    def __enter__(self) -> "PagoUnitOfWork":
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
        self.pagos = PagoRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            if not self._external_session:
                self.session.close()
