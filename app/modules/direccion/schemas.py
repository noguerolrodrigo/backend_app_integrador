from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class DireccionEntregaCreate(SQLModel):
    """Schema para crear una dirección de entrega (admin, con usuario_id explícito)"""
    usuario_id: int
    alias: str
    calle: str
    numero: str
    apartamento: Optional[str] = None
    localidad: str
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    notas: Optional[str] = None
    es_principal: bool = False


class DireccionEntregaCreateCliente(SQLModel):
    """Schema para crear una dirección (cliente autenticado, sin usuario_id)
    
    El usuario_id se obtiene del token JWT, no del body.
    """
    alias: str
    calle: str
    numero: str
    apartamento: Optional[str] = None
    localidad: str
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    notas: Optional[str] = None
    es_principal: bool = False


class DireccionEntregaUpdate(SQLModel):
    """Schema para actualizar una dirección de entrega"""
    alias: Optional[str] = None
    calle: Optional[str] = None
    numero: Optional[str] = None
    apartamento: Optional[str] = None
    localidad: Optional[str] = None
    codigo_postal: Optional[str] = None
    provincia: Optional[str] = None
    notas: Optional[str] = None
    es_principal: Optional[bool] = None


class DireccionEntregaRead(SQLModel):
    """Schema para leer una dirección de entrega"""
    id: int
    usuario_id: int
    alias: str
    calle: str
    numero: str
    apartamento: Optional[str]
    localidad: str
    codigo_postal: Optional[str]
    provincia: Optional[str]
    notas: Optional[str]
    es_principal: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class DireccionEntregaReadSimple(SQLModel):
    """Schema simplificado para listados"""
    id: int
    alias: str
    localidad: str
    numero: str
    calle: str
    es_principal: bool


class DireccionEntregaReadCompleta(SQLModel):
    """Schema con dirección completa formateada"""
    id: int
    alias: str
    direccion_completa: str
    es_principal: bool
    created_at: datetime


class DireccionCreatedResponse(SQLModel):
    """Response al crear una dirección"""
    mensaje: str
    direccion_id: int
    alias: str
    es_principal: bool


class DireccionActualizadaResponse(SQLModel):
    """Response al actualizar una dirección"""
    mensaje: str
    direccion_id: int
    alias: str
    es_principal: bool
    updated_at: datetime


class DireccionPrincipalResponse(SQLModel):
    """Response al marcar dirección como principal"""
    mensaje: str
    direccion_id: int
    alias: str
    es_principal: bool
