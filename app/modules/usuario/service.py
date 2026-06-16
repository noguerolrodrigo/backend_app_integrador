from datetime import datetime
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.security import hash_password, verify_password
from app.modules.usuario.models import Usuario, Rol, UsuarioRol
from app.modules.usuario.schemas import UsuarioCreate, UsuarioUpdate, RolCreate, RolUpdate
from app.modules.usuario.usuario_uow import UsuarioUnitOfWork


class UsuarioService:
    """Servicio de lógica de negocio para Usuarios"""

    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def crear_usuario(self, data: UsuarioCreate) -> Usuario:
        """Crea un nuevo usuario con contraseña hasheada"""
        # Verificar si el email ya existe
        if self.uow.usuarios.exists_email(data.email):
            raise ValueError(f"El email {data.email} ya está registrado")

        # Hashear la contraseña
        password_hash = self._hash_password(data.password)

        usuario = Usuario(
            email=data.email,
            nombre=data.nombre,
            apellido=data.apellido,
            password_hash=password_hash,
            activo=data.activo
        )

        self.uow.usuarios.create(usuario)
        # Recargar con roles eager-loaded para evitar DetachedInstanceError al serializar
        statement = (
            select(Usuario)
            .where(Usuario.id == usuario.id)
            .options(selectinload(Usuario.roles))
        )
        return self.uow.session.exec(statement).first()

    def obtener_usuario_por_id(self, usuario_id: int) -> Optional[Usuario]:
        """Obtiene un usuario por ID"""
        return self.uow.usuarios.get_by_id(usuario_id)

    def obtener_usuario_por_email(self, email: str) -> Optional[Usuario]:
        """Obtiene un usuario por email"""
        return self.uow.usuarios.get_by_email(email)

    def listar_usuarios(self, skip: int = 0, limit: int = 100) -> list[Usuario]:
        """Lista todos los usuarios activos"""
        return self.uow.usuarios.get_all(skip=skip, limit=limit, include_deleted=False)

    def actualizar_usuario(self, usuario_id: int, data: UsuarioUpdate) -> Optional[Usuario]:
        """Actualiza los datos de un usuario"""
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        # Validar email único si se está actualizando
        if data.email and data.email != usuario.email:
            if self.uow.usuarios.exists_email(data.email, exclude_id=usuario_id):
                raise ValueError(f"El email {data.email} ya está registrado")

        return self.uow.usuarios.update(usuario, data.model_dump(exclude_unset=True))

    def cambiar_contrasena(self, usuario_id: int, password_actual: str, password_nueva: str) -> Usuario:
        """Cambia la contraseña de un usuario"""
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        # Verificar contraseña actual
        if not self._verify_password(password_actual, usuario.password_hash):
            raise ValueError("Contraseña actual incorrecta")

        # Hashear y actualizar nueva contraseña
        usuario.password_hash = self._hash_password(password_nueva)
        usuario.updated_at = datetime.utcnow()
        self.uow.session.add(usuario)
        self.uow.session.flush()

        return usuario

    def eliminar_usuario(self, usuario_id: int, hard_delete: bool = False) -> None:
        """Elimina un usuario (soft delete por defecto)"""
        usuario = self.uow.usuarios.get_by_id(usuario_id, include_deleted=False)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        if hard_delete:
            self.uow.usuarios.hard_delete(usuario)
        else:
            self.uow.usuarios.soft_delete(usuario)

    def restaurar_usuario(self, usuario_id: int) -> Usuario:
        """Restaura un usuario eliminado"""
        usuario = self.uow.usuarios.get_by_id(usuario_id, include_deleted=True)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        return self.uow.usuarios.restore(usuario)

    def verificar_contrasena(self, email: str, password: str) -> Optional[Usuario]:
        """Verifica el email y contraseña de un usuario (útil para login)"""
        usuario = self.uow.usuarios.get_by_email(email)
        if not usuario or not usuario.is_active():
            return None

        if self._verify_password(password, usuario.password_hash):
            return usuario

        return None

    @staticmethod
    def _hash_password(password: str) -> str:
        """Genera hash bcrypt con 12 salt rounds (adaptativo y seguro)"""
        return hash_password(password)

    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verifica una contraseña contra su hash bcrypt"""
        return verify_password(password, password_hash)


class RolService:
    """Servicio de lógica de negocio para Roles"""

    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def crear_rol(self, data: RolCreate) -> Rol:
        """Crea un nuevo rol"""
        # Verificar si el código ya existe
        if self.uow.roles.exists_codigo(data.codigo):
            raise ValueError(f"El código de rol '{data.codigo}' ya existe")

        rol = Rol(
            nombre=data.nombre,
            codigo=data.codigo,
            descripcion=data.descripcion
        )

        return self.uow.roles.create(rol)

    def obtener_rol_por_id(self, rol_id: int) -> Optional[Rol]:
        """Obtiene un rol por ID"""
        return self.uow.roles.get_by_id(rol_id)

    def obtener_rol_por_codigo(self, codigo: str) -> Optional[Rol]:
        """Obtiene un rol por código"""
        return self.uow.roles.get_by_codigo(codigo)

    def listar_roles(self, skip: int = 0, limit: int = 100) -> list[Rol]:
        """Lista todos los roles activos"""
        return self.uow.roles.get_all(skip=skip, limit=limit, include_deleted=False)

    def actualizar_rol(self, rol_id: int, data: RolUpdate) -> Optional[Rol]:
        """Actualiza un rol"""
        rol = self.uow.roles.get_by_id(rol_id)
        if not rol:
            raise ValueError(f"Rol con ID {rol_id} no encontrado")

        # Validar código único si se está actualizando
        if data.codigo and data.codigo != rol.codigo:
            if self.uow.roles.exists_codigo(data.codigo, exclude_id=rol_id):
                raise ValueError(f"El código de rol '{data.codigo}' ya existe")

        return self.uow.roles.update(rol, data.model_dump(exclude_unset=True))

    def eliminar_rol(self, rol_id: int, hard_delete: bool = False) -> None:
        """Elimina un rol (soft delete por defecto)"""
        rol = self.uow.roles.get_by_id(rol_id, include_deleted=False)
        if not rol:
            raise ValueError(f"Rol con ID {rol_id} no encontrado")

        if hard_delete:
            self.uow.roles.hard_delete(rol)
        else:
            self.uow.roles.soft_delete(rol)

    def restaurar_rol(self, rol_id: int) -> Rol:
        """Restaura un rol eliminado"""
        rol = self.uow.roles.get_by_id(rol_id, include_deleted=True)
        if not rol:
            raise ValueError(f"Rol con ID {rol_id} no encontrado")

        return self.uow.roles.restore(rol)


class UsuarioRolService:
    """Servicio de lógica de negocio para la relación Usuario-Rol (RBAC)"""

    def __init__(self, uow: UsuarioUnitOfWork):
        self.uow = uow

    def asignar_rol_a_usuario(self, usuario_id: int, rol_id: int) -> UsuarioRol:
        """Asigna un rol a un usuario"""
        # Verificar que exista el usuario y el rol
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        rol = self.uow.roles.get_by_id(rol_id)
        if not rol:
            raise ValueError(f"Rol con ID {rol_id} no encontrado")

        return self.uow.usuarios_roles.asignar_rol(usuario_id, rol_id)

    def desasignar_rol_de_usuario(self, usuario_id: int, rol_id: int) -> None:
        """Desasigna un rol de un usuario"""
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        rol = self.uow.roles.get_by_id(rol_id)
        if not rol:
            raise ValueError(f"Rol con ID {rol_id} no encontrado")

        self.uow.usuarios_roles.desasignar_rol(usuario_id, rol_id)

    def obtener_roles_usuario(self, usuario_id: int) -> list[Rol]:
        """Obtiene todos los roles de un usuario"""
        usuario = self.uow.usuarios.get_by_id(usuario_id)
        if not usuario:
            raise ValueError(f"Usuario con ID {usuario_id} no encontrado")

        return self.uow.usuarios_roles.get_roles_by_usuario(usuario_id)

    def usuario_tiene_rol(self, usuario_id: int, rol_id: int) -> bool:
        """Verifica si un usuario tiene un rol específico"""
        return self.uow.usuarios_roles.usuario_tiene_rol(usuario_id, rol_id)

    def usuario_tiene_codigo_rol(self, usuario_id: int, codigo_rol: str) -> bool:
        """Verifica si un usuario tiene un rol por código"""
        return self.uow.usuarios_roles.usuario_tiene_codigo_rol(usuario_id, codigo_rol)
