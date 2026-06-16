from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric
from sqlmodel import SQLModel, Field, Column


class ProductoIngrediente(SQLModel, table=True):
    __tablename__ = "producto_ingrediente"

    producto_id: Optional[int] = Field(
        default=None,
        foreign_key="producto.id",
        primary_key=True,
    )

    ingrediente_id: Optional[int] = Field(
        default=None,
        foreign_key="ingrediente.id",
        primary_key=True,
    )

    es_removible: bool = Field(default=False, nullable=False)

    cantidad: Optional[Decimal] = Field(
        default=None,
        sa_column=Column(Numeric(10, 3), nullable=False, server_default="1.000"),
    )

    unidad_medida_id: Optional[int] = Field(
        default=None,
        foreign_key="unidad_medida.id",
        nullable=False,
    )
