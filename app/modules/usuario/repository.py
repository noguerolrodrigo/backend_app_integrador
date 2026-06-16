from datetime import datetime
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.base_repository import BaseRepository
from app.modules.usuario.models import Usuario, Rol, UsuarioRol


class UsuarioRepository(BaseRepository[Usuario]):
    """Repositorio para operaciones de Usuario"""

    def __init__(self, session: Session):
        super().__init__(Usuario, session)

    def get_by_id(self, usuario_id: int, include_deleted: bool = False) -> Optional[Usuario]:
        """Obtiene un usuario por ID con roles eager-loaded"""
        query = (
            select(Usuario)
            .where(Usuario.id == usuario_id)
            .options(selectinload(Usuario.roles))
        )
        if not include_deleted:
            query = query.where(Usuario.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_by_email(self, email: str, include_deleted: bool = False) -> Optional[Usuario]:
        """Obtiene un usuario por email"""
        query = select(Usuario).where(Usuario.email == email)
        if not include_deleted:
            query = query.where(Usuario.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Usuario]:
        """Obtiene todos los usuarios con roles eager-loaded"""
        query = select(Usuario).options(selectinload(Usuario.roles))
        if not include_deleted:
            query = query.where(Usuario.deleted_at.is_(None))
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def create(self, usuario: Usuario) -> Usuario:
        """Crea un nuevo usuario (commit manejado por UoW)"""
        return self.add(usuario)

    def update(self, usuario: Usuario, data: dict) -> Usuario:
        """Actualiza un usuario (commit manejado por UoW)"""
        excluded_fields = {"id", "created_at", "deleted_at"}
        for key, value in data.items():
            if key not in excluded_fields and value is not None:
                setattr(usuario, key, value)

        usuario.updated_at = datetime.utcnow()
        self.session.add(usuario)
        self.session.flush()
        return usuario

    def soft_delete(self, usuario: Usuario) -> Usuario:
        """Elimina un usuario de forma lógica (soft delete, commit manejado por UoW)"""
        usuario.deleted_at = datetime.utcnow()
        usuario.updated_at = datetime.utcnow()
        self.session.add(usuario)
        self.session.flush()
        return usuario

    def restore(self, usuario: Usuario) -> Usuario:
        """Restaura un usuario eliminado (commit manejado por UoW)"""
        usuario.deleted_at = None
        usuario.updated_at = datetime.utcnow()
        self.session.add(usuario)
        self.session.flush()
        return usuario

    def hard_delete(self, usuario: Usuario) -> None:
        """Elimina un usuario de forma permanente (commit manejado por UoW)"""
        self.session.delete(usuario)
        self.session.flush()

    def exists_email(self, email: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si un email ya existe"""
        query = select(Usuario).where(
            Usuario.email == email,
            Usuario.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.where(Usuario.id != exclude_id)
        return self.session.exec(query).first() is not None


class RolRepository(BaseRepository[Rol]):
    """Repositorio para operaciones de Rol"""

    def __init__(self, session: Session):
        super().__init__(Rol, session)

    def get_by_id(self, rol_id: int, include_deleted: bool = False) -> Optional[Rol]:
        """Obtiene un rol por ID"""
        if include_deleted:
            return super().get_by_id(rol_id)
        rol = super().get_by_id(rol_id)
        if rol and rol.is_deleted():
            return None
        return rol

    def get_by_codigo(self, codigo: str, include_deleted: bool = False) -> Optional[Rol]:
        """Obtiene un rol por código"""
        query = select(Rol).where(Rol.codigo == codigo)
        if not include_deleted:
            query = query.where(Rol.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Rol]:
        """Obtiene todos los roles"""
        query = select(Rol)
        if not include_deleted:
            query = query.where(Rol.deleted_at.is_(None))
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def create(self, rol: Rol) -> Rol:
        """Crea un nuevo rol (commit manejado por UoW)"""
        return self.add(rol)

    def update(self, rol: Rol, data: dict) -> Rol:
        """Actualiza un rol (commit manejado por UoW)"""
        excluded_fields = {"id", "created_at", "deleted_at"}
        for key, value in data.items():
            if key not in excluded_fields and value is not None:
                setattr(rol, key, value)

        rol.updated_at = datetime.utcnow()
        self.session.add(rol)
        self.session.flush()
        return rol

    def soft_delete(self, rol: Rol) -> Rol:
        """Elimina un rol de forma lógica (soft delete, commit manejado por UoW)"""
        rol.deleted_at = datetime.utcnow()
        rol.updated_at = datetime.utcnow()
        self.session.add(rol)
        self.session.flush()
        return rol

    def restore(self, rol: Rol) -> Rol:
        """Restaura un rol eliminado (commit manejado por UoW)"""
        rol.deleted_at = None
        rol.updated_at = datetime.utcnow()
        self.session.add(rol)
        self.session.flush()
        return rol

    def hard_delete(self, rol: Rol) -> None:
        """Elimina un rol de forma permanente (commit manejado por UoW)"""
        self.session.delete(rol)
        self.session.flush()

    def exists_codigo(self, codigo: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si un código de rol ya existe"""
        query = select(Rol).where(
            Rol.codigo == codigo,
            Rol.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.where(Rol.id != exclude_id)
        return self.session.exec(query).first() is not None


class UsuarioRolRepository(BaseRepository[UsuarioRol]):
    """Repositorio para operaciones de la relación Usuario-Rol"""

    def __init__(self, session: Session):
        super().__init__(UsuarioRol, session)

    def asignar_rol(self, usuario_id: int, rol_id: int) -> UsuarioRol:
        """Asigna un rol a un usuario (commit manejado por UoW)"""
        query = select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol_id == rol_id
        )
        if self.session.exec(query).first():
            raise ValueError(f"El usuario {usuario_id} ya tiene el rol {rol_id}")

        usuario_rol = UsuarioRol(usuario_id=usuario_id, rol_id=rol_id)
        self.session.add(usuario_rol)
        self.session.flush()
        return usuario_rol

    def desasignar_rol(self, usuario_id: int, rol_id: int) -> None:
        """Desasigna un rol de un usuario (commit manejado por UoW)"""
        query = select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol_id == rol_id
        )
        usuario_rol = self.session.exec(query).first()
        if usuario_rol:
            self.session.delete(usuario_rol)
            self.session.flush()

    def get_roles_by_usuario(self, usuario_id: int) -> list[Rol]:
        """Obtiene todos los roles de un usuario"""
        query = select(Rol).join(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario_id,
            Rol.deleted_at.is_(None)
        )
        return self.session.exec(query).all()

    def usuario_tiene_rol(self, usuario_id: int, rol_id: int) -> bool:
        """Verifica si un usuario tiene un rol específico"""
        query = select(UsuarioRol).where(
            UsuarioRol.usuario_id == usuario_id,
            UsuarioRol.rol_id == rol_id
        )
        return self.session.exec(query).first() is not None

    def usuario_tiene_codigo_rol(self, usuario_id: int, codigo_rol: str) -> bool:
        """Verifica si un usuario tiene un rol por código"""
        query = select(UsuarioRol).join(Rol).where(
            UsuarioRol.usuario_id == usuario_id,
            Rol.codigo == codigo_rol,
            Rol.deleted_at.is_(None)
        )
        return self.session.exec(query).first() is not None
