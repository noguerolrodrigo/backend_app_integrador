from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel


class PagoCreate(SQLModel):
    pedido_id: int
    token: str
    installments: int = 1
    payment_method_id: str
    issuer_id: Optional[int] = None


class PagoRead(SQLModel):
    id: int
    pedido_id: int
    mp_payment_id: Optional[int]
    mp_status: str
    mp_status_detail: Optional[str]
    transaction_amount: Decimal
    payment_method_id: Optional[str]
    external_reference: str
    idempotency_key: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
