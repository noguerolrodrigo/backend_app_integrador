from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_current_user, require_role
from app.modules.usuario.service import UsuarioService, RolService, UsuarioRolService
from app.modules.usuario.models import Usuario
from app.modules.usuario.schemas import (
    UsuarioCreate, UsuarioUpdate, UsuarioRead, UsuarioReadSimple,
    UsuarioChangePassword,
    RolCreate, RolUpdate, RolRead, RolReadSimple,
    AsignarRolUsuario
)
from app.modules.usuario.usuario_uow import UsuarioUnitOfWork

router = APIRouter(prefix="/api/v1", tags=["Usuarios y Roles"])


# ==================== ENDPOINTS DE USUARIO ====================


@router.get("/usuarios", response_model=list[UsuarioRead], status_code=status.HTTP_200_OK)
def listar_usuarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Lista todos los usuarios (paginado)"""
    with UsuarioUnitOfWork() as uow:
        service = UsuarioService(uow)
        return service.listar_usuarios(skip=skip, limit=limit)


@router.get("/usuarios/{usuario_id}", response_model=UsuarioRead, status_code=status.HTTP_200_OK)
def obtener_usuario(
    usuario_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Obtiene un usuario por ID"""
    with UsuarioUnitOfWork() as uow:
        service = UsuarioService(uow)
        usuario = service.obtener_usuario_por_id(usuario_id)

        if not usuario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Usuario con ID {usuario_id} no encontrado"
            )

        return usuario


@router.post("/usuarios", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario(
    data: UsuarioCreate,
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Crea un nuevo usuario"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioService(uow)
            usuario = service.crear_usuario(data)
            return usuario
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/usuarios/{usuario_id}", response_model=UsuarioRead, status_code=status.HTTP_200_OK)
def actualizar_usuario(
    data: UsuarioUpdate,
    usuario_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Actualiza un usuario"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioService(uow)
            usuario = service.actualizar_usuario(usuario_id, data)
            return usuario
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/usuarios/{usuario_id}/cambiar-contrasena", response_model=UsuarioRead)
def cambiar_contrasena(
    data: UsuarioChangePassword,
    usuario_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Cambia la contraseña de un usuario"""
    # Validar que las contraseñas nuevas coincidan
    if data.password_nueva != data.password_confirmacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Las contraseñas nuevas no coinciden"
        )

    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioService(uow)
            usuario = service.cambiar_contrasena(
                usuario_id,
                data.password_actual,
                data.password_nueva
            )
            return usuario
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: int = Path(..., gt=0),
    hard_delete: bool = Query(False),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Elimina un usuario (soft delete por defecto)"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioService(uow)
            service.eliminar_usuario(usuario_id, hard_delete=hard_delete)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/usuarios/{usuario_id}/restaurar", response_model=UsuarioRead)
def restaurar_usuario(
    usuario_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Restaura un usuario eliminado"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioService(uow)
            usuario = service.restaurar_usuario(usuario_id)
            return usuario
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== ENDPOINTS DE ROL ====================


@router.get("/roles", response_model=list[RolRead], status_code=status.HTTP_200_OK)
def listar_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Lista todos los roles"""
    with UsuarioUnitOfWork() as uow:
        service = RolService(uow)
        return service.listar_roles(skip=skip, limit=limit)


@router.get("/roles/{rol_id}", response_model=RolRead, status_code=status.HTTP_200_OK)
def obtener_rol(
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Obtiene un rol por ID"""
    with UsuarioUnitOfWork() as uow:
        service = RolService(uow)
        rol = service.obtener_rol_por_id(rol_id)

        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rol con ID {rol_id} no encontrado"
            )

        return rol


@router.post("/roles", response_model=RolRead, status_code=status.HTTP_201_CREATED)
def crear_rol(
    data: RolCreate,
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Crea un nuevo rol"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = RolService(uow)
            rol = service.crear_rol(data)
            return rol
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/roles/{rol_id}", response_model=RolRead, status_code=status.HTTP_200_OK)
def actualizar_rol(
    data: RolUpdate,
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Actualiza un rol"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = RolService(uow)
            rol = service.actualizar_rol(rol_id, data)
            return rol
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_rol(
    rol_id: int = Path(..., gt=0),
    hard_delete: bool = Query(False),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Elimina un rol (soft delete por defecto)"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = RolService(uow)
            service.eliminar_rol(rol_id, hard_delete=hard_delete)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/roles/{rol_id}/restaurar", response_model=RolRead)
def restaurar_rol(
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Restaura un rol eliminado"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = RolService(uow)
            rol = service.restaurar_rol(rol_id)
            return rol
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


# ==================== ENDPOINTS DE ASIGNACIÓN DE ROLES ====================


@router.post("/usuarios/{usuario_id}/roles/{rol_id}", status_code=status.HTTP_201_CREATED)
def asignar_rol_a_usuario(
    usuario_id: int = Path(..., gt=0),
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Asigna un rol a un usuario"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioRolService(uow)
            service.asignar_rol_a_usuario(usuario_id, rol_id)
            return {"mensaje": "Rol asignado exitosamente"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/usuarios/{usuario_id}/roles/{rol_id}", status_code=status.HTTP_204_NO_CONTENT)
def desasignar_rol_de_usuario(
    usuario_id: int = Path(..., gt=0),
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Desasigna un rol de un usuario"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioRolService(uow)
            service.desasignar_rol_de_usuario(usuario_id, rol_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/usuarios/{usuario_id}/roles", response_model=list[RolReadSimple])
def obtener_roles_usuario(
    usuario_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Obtiene todos los roles de un usuario"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioRolService(uow)
            return service.obtener_roles_usuario(usuario_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/usuarios/{usuario_id}/tiene-rol/{rol_id}", response_model=dict)
def usuario_tiene_rol(
    usuario_id: int = Path(..., gt=0),
    rol_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"]))
):
    """Verifica si un usuario tiene un rol específico"""
    try:
        with UsuarioUnitOfWork() as uow:
            service = UsuarioRolService(uow)
            tiene_rol = service.usuario_tiene_rol(usuario_id, rol_id)
            return {"usuario_id": usuario_id, "rol_id": rol_id, "tiene_rol": tiene_rol}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
