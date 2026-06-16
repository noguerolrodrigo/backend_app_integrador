from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class UnidadMedida(SQLModel, table=True):
    __tablename__ = "unidad_medida"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=50, unique=True, nullable=False)
    simbolo: str = Field(max_length=10, unique=True, nullable=False)
    tipo: str = Field(max_length=20, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
