from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class CategoriaCreate(SQLModel):
    nombre: str
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaUpdate(SQLModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_url: Optional[str] = None
    parent_id: Optional[int] = None


class CategoriaRead(SQLModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    imagen_url: Optional[str]
    parent_id: Optional[int]
    deleted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


class CategoriaReadSimple(SQLModel):
    id: int
    nombre: str


# --- Public endpoint schemas ---

class CategoriaPublicRead(SQLModel):
    """Same as CategoriaRead but without deleted_at — for public consumption"""
    id: int
    nombre: str
    descripcion: Optional[str]
    imagen_url: Optional[str]
    parent_id: Optional[int]
    created_at: datetime
    updated_at: datetime


class CategoriaPublicQuery(SQLModel):
    limit: int = 20
    offset: int = 0
    parent_id: Optional[int] = None


class CategoriaPublicResponse(SQLModel):
    items: list[CategoriaPublicRead]
    total: int
    limit: int
    offset: int
