from typing import Optional

from sqlmodel import select

from app.core.base_repository import BaseRepository
from app.modules.pagos.model import Pago


class PagoRepository(BaseRepository[Pago]):
    def __init__(self, session):
        super().__init__(Pago, session)

    def get_by_pedido_id(self, pedido_id: int) -> Optional[Pago]:
        return self.session.exec(
            select(Pago).where(Pago.pedido_id == pedido_id)
        ).first()

    def get_by_mp_payment_id(self, mp_payment_id: int) -> Optional[Pago]:
        return self.session.exec(
            select(Pago).where(Pago.mp_payment_id == mp_payment_id)
        ).first()

    def get_by_idempotency_key(self, key: str) -> Optional[Pago]:
        return self.session.exec(
            select(Pago).where(Pago.idempotency_key == key)
        ).first()

    def get_by_external_reference(self, external_reference: str) -> Optional[Pago]:
        return self.session.exec(
            select(Pago).where(Pago.external_reference == external_reference)
        ).first()
