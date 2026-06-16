from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


# ==================== SCHEMAS DE ROL ====================

class RolCreate(SQLModel):
    """Schema para crear un nuevo rol"""
    nombre: str
    codigo: str
    descripcion: Optional[str] = None


class RolUpdate(SQLModel):
    """Schema para actualizar un rol"""
    nombre: Optional[str] = None
    codigo: Optional[str] = None
    descripcion: Optional[str] = None


class RolRead(SQLModel):
    """Schema para leer un rol (respuesta)"""
    id: int
    nombre: str
    codigo: str
    descripcion: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]


class RolReadSimple(SQLModel):
    """Schema simplificado de rol para relaciones"""
    id: int
    nombre: str
    codigo: str


# ==================== SCHEMAS DE USUARIO ====================

class UsuarioCreate(SQLModel):
    """Schema para crear un nuevo usuario"""
    email: str
    nombre: str
    apellido: str
    password: str
    activo: bool = True


class UsuarioUpdate(SQLModel):
    """Schema para actualizar un usuario"""
    email: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    activo: Optional[bool] = None


class UsuarioChangePassword(SQLModel):
    """Schema para cambiar la contraseña de un usuario"""
    password_actual: str
    password_nueva: str
    password_confirmacion: str


class UsuarioRead(SQLModel):
    """Schema para leer un usuario (respuesta completa)"""
    id: int
    email: str
    nombre: str
    apellido: str
    activo: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    roles: list[RolReadSimple] = []


class UsuarioReadSimple(SQLModel):
    """Schema simplificado de usuario"""
    id: int
    email: str
    nombre: str
    apellido: str
    activo: bool


class UsuarioReadProfile(SQLModel):
    """Schema para el perfil del usuario autenticado"""
    id: int
    email: str
    nombre: str
    apellido: str
    activo: bool
    created_at: datetime
    roles: list[RolReadSimple] = []


# ==================== SCHEMAS DE RELACIÓN ====================

class AsignarRolUsuario(SQLModel):
    """Schema para asignar un rol a un usuario"""
    usuario_id: int
    rol_id: int


class DesasignarRolUsuario(SQLModel):
    """Schema para desasignar un rol de un usuario"""
    usuario_id: int
    rol_id: int
