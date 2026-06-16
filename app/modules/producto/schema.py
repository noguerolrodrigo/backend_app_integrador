from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel

from app.modules.categoria.schema import CategoriaReadSimple
from app.modules.ingrediente.schema import IngredienteReadSimple

class ProductoBase(SQLModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_base: float
    imagenes_url: list[str] = Field(default_factory=list)
    stock_cantidad: int = 0
    disponible: bool = True
    unidad_venta_id: Optional[int] = None


class ProductoCreate(ProductoBase):
    pass

class ProductoUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    precio_base: Optional[float] = None
    imagenes_url: Optional[list[str]] = None
    stock_cantidad: Optional[int] = None
    disponible: Optional[bool] = None


class ProductoUpdateDisponibilidad(SQLModel):
    disponible: bool


class ImagenProductoUpdate(SQLModel):
    imagenes_url: list[str]


class ProductoRead(ProductoBase):
    id: int

    categorias: List[CategoriaReadSimple] = Field(default_factory=list)
    ingredientes: List[IngredienteReadSimple] = Field(default_factory=list)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None