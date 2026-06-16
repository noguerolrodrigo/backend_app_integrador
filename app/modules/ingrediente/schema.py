from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class IngredienteBase(SQLModel):
    nombre: str
    descripcion: Optional[str] = None
    es_alergeno: bool = False
    stock_cantidad: int = 0


class IngredienteCreate(IngredienteBase):
    pass


class IngredienteUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    es_alergeno: Optional[bool] = None
    stock_cantidad: Optional[int] = None


class IngredienteRead(IngredienteBase):
    id: int
    es_alergeno: bool
    stock_cantidad: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class IngredienteReadSimple(SQLModel):
    id: int
    nombre: str