from datetime import datetime
from sqlmodel import SQLModel, Field


class ProductoCategoria(SQLModel, table=True):
    __tablename__ = "producto_categoria"

    producto_id: int = Field(
        foreign_key="producto.id",
        primary_key=True
    )

    categoria_id: int = Field(
        foreign_key="categoria.id",
        primary_key=True
    )

    es_principal: bool = Field(default=False)

    created_at: datetime = Field(default_factory=datetime.utcnow)