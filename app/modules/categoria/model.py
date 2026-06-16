from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship
from app.modules.producto_categoria.model import ProductoCategoria

if TYPE_CHECKING:
    from app.modules.producto.model import Producto


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"

    id: Optional[int] = Field(default=None, primary_key=True)

    nombre: str = Field(max_length=100, unique=True)
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = Field(default=None, foreign_key="categoria.id")

    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Self-referencing hierarchy
    parent: Optional["Categoria"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "Categoria.id"},
    )
    children: List["Categoria"] = Relationship(back_populates="parent")

    # Many-to-many with Producto
    productos: List["Producto"] = Relationship(
        back_populates="categorias",
        link_model=ProductoCategoria,
    )

    def is_deleted(self) -> bool:
        return self.deleted_at is not None
