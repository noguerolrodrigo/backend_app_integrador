from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    pass


class UsuarioRol(SQLModel, table=True):
    """Tabla intermedia para la relación N:N entre Usuario y Rol"""
    __tablename__ = "usuario_rol"

    usuario_id: Optional[int] = Field(
        default=None,
        foreign_key="usuario.id",
        primary_key=True
    )
    rol_id: Optional[int] = Field(
        default=None,
        foreign_key="rol.id",
        primary_key=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Rol(SQLModel, table=True):
    """Modelo de Rol para RBAC"""
    __tablename__ = "rol"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(max_length=100, unique=True, index=True)
    codigo: str = Field(max_length=50, unique=True, index=True)
    descripcion: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    usuarios: List["Usuario"] = Relationship(
        back_populates="roles",
        link_model=UsuarioRol
    )

    def is_deleted(self) -> bool:
        """Verifica si el rol está eliminado (soft delete)"""
        return self.deleted_at is not None


class Usuario(SQLModel, table=True):
    """Modelo de Usuario con soporte para soft delete"""
    __tablename__ = "usuario"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, unique=True, index=True)
    nombre: str = Field(max_length=255)
    apellido: str = Field(max_length=255)
    password_hash: str = Field(max_length=255)
    activo: bool = Field(default=True)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)

    roles: List["Rol"] = Relationship(
        back_populates="usuarios",
        link_model=UsuarioRol
    )

    def is_deleted(self) -> bool:
        """Verifica si el usuario está eliminado (soft delete)"""
        return self.deleted_at is not None

    def is_active(self) -> bool:
        """Verifica si el usuario está activo y no eliminado"""
        return self.activo and not self.is_deleted()
