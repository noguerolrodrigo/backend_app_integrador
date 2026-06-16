from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class UnidadMedidaBase(SQLModel):
    nombre: str = Field(max_length=50)
    simbolo: str = Field(max_length=10)
    tipo: str = Field(max_length=20)


class UnidadMedidaCreate(UnidadMedidaBase):
    pass


class UnidadMedidaUpdate(SQLModel):
    nombre: Optional[str] = Field(None, max_length=50)
    simbolo: Optional[str] = Field(None, max_length=10)
    tipo: Optional[str] = Field(None, max_length=20)


class UnidadMedidaRead(UnidadMedidaBase):
    id: int
    created_at: datetime
