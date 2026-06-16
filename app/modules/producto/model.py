from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON

from app.modules.producto_categoria.model import ProductoCategoria
from app.modules.producto_ingrediente.model import ProductoIngrediente

if TYPE_CHECKING:
    from app.modules.categoria.model import Categoria
    from app.modules.ingrediente.model import Ingrediente


class Producto(SQLModel, table=True):
    __tablename__ = "producto"

    id: Optional[int] = Field(default=None, primary_key=True)

    nombre: str = Field(max_length=150, nullable=False)
    descripcion: Optional[str] = None
    precio_base: float = Field(nullable=False, ge=0)

    imagenes_url: Optional[list[str]] = Field(default=None, sa_column=Column(JSON))

    stock_cantidad: int = Field(default=0, ge=0)
    disponible: bool = Field(default=True)
    unidad_venta_id: Optional[int] = Field(default=None, foreign_key="unidad_medida.id", nullable=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    def is_deleted(self) -> bool:
        """Verifica si el producto está eliminado (soft delete)"""
        return self.deleted_at is not None

    def is_available(self) -> bool:
        """Verifica si el producto está disponible y no eliminado"""
        return self.disponible and not self.is_deleted()

    categorias: List["Categoria"] = Relationship(
        back_populates="productos",
        link_model=ProductoCategoria
    )

    ingredientes: List["Ingrediente"] = Relationship(
        back_populates="productos",
        link_model=ProductoIngrediente
    )