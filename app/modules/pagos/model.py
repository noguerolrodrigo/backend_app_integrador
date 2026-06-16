from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Numeric
from sqlmodel import SQLModel, Field, Column, Relationship

if TYPE_CHECKING:
    from app.modules.pedido.models import Pedido


class Pago(SQLModel, table=True):
    __tablename__ = "pago"

    id: Optional[int] = Field(default=None, primary_key=True)

    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, unique=True, index=True)

    mp_payment_id: Optional[int] = Field(default=None, nullable=True, unique=True)
    mp_status: str = Field(max_length=30, nullable=False)
    mp_status_detail: Optional[str] = Field(default=None, max_length=100, nullable=True)
    transaction_amount: Decimal = Field(sa_column=Column(Numeric(10, 2), nullable=False))
    payment_method_id: Optional[str] = Field(default=None, max_length=50, nullable=True)
    external_reference: str = Field(max_length=100, nullable=False, unique=True)
    idempotency_key: str = Field(max_length=100, nullable=False, unique=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    pedido: Optional["Pedido"] = Relationship()
