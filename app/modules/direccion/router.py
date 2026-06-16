from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_current_user, require_role
from app.modules.direccion.service import DireccionEntregaService
from app.modules.direccion.direccion_uow import DireccionUnitOfWork
from app.modules.direccion.schemas import (
    DireccionEntregaCreate,
    DireccionEntregaCreateCliente,
    DireccionEntregaUpdate,
    DireccionEntregaRead,
    DireccionEntregaReadSimple,
    DireccionEntregaReadCompleta,
    DireccionCreatedResponse,
    DireccionActualizadaResponse,
    DireccionPrincipalResponse,
)
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/api/v1/direcciones", tags=["Direcciones de Entrega"])


# ==================== ENDPOINTS DE CREACIÓN ====================


@router.post("/", response_model=DireccionCreatedResponse, status_code=status.HTTP_201_CREATED)
def crear_direccion(
    data: DireccionEntregaCreateCliente,
    current_user: Usuario = Depends(get_current_user),
):
    """Crea una nueva dirección de entrega para el usuario autenticado"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.crear_direccion(data, usuario_id=current_user.id)

            return DireccionCreatedResponse(
                mensaje="Dirección creada exitosamente",
                direccion_id=direccion.id,
                alias=direccion.alias,
                es_principal=direccion.es_principal,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear dirección: {str(e)}",
        )


# ==================== ENDPOINTS DE LECTURA (CLIENTE) ====================


@router.get("/", response_model=list[DireccionEntregaReadSimple])
def listar_mis_direcciones(
    current_user: Usuario = Depends(get_current_user),
):
    """Lista todas las direcciones activas del usuario autenticado"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            return service.obtener_direcciones_usuario(current_user.id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar direcciones: {str(e)}",
        )


@router.get("/{direccion_id}", response_model=DireccionEntregaRead)
def obtener_direccion(
    direccion_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene una dirección específica por ID (solo si pertenece al usuario autenticado)"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.obtener_direccion_por_id(direccion_id)

            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dirección {direccion_id} no encontrada",
                )

            # Verificar pertenencia
            if direccion.usuario_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Dirección {direccion_id} no encontrada",
                )

            return direccion

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dirección: {str(e)}",
        )


# ==================== ENDPOINTS DE ADMIN (LECTURA) ====================


@router.get("/usuario/{usuario_id}", response_model=list[DireccionEntregaReadCompleta])
def listar_direcciones_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """[ADMIN] Lista todas las direcciones de un usuario con dirección completa formateada"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direcciones = service.obtener_direcciones_usuario(usuario_id)

            return [
                DireccionEntregaReadCompleta(
                    id=d.id,
                    alias=d.alias,
                    direccion_completa=d.direccion_completa(),
                    es_principal=d.es_principal,
                    created_at=d.created_at,
                )
                for d in direcciones
            ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar direcciones: {str(e)}",
        )


@router.get("/usuario/{usuario_id}/principal", response_model=DireccionEntregaRead)
def obtener_principal_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """[ADMIN] Obtiene la dirección principal de un usuario"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.obtener_principal_usuario(usuario_id)

            if not direccion:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Usuario {usuario_id} no tiene dirección principal",
                )

            return direccion

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener dirección principal: {str(e)}",
        )


# ==================== ENDPOINTS DE ACTUALIZACIÓN ====================


@router.patch("/{direccion_id}", response_model=DireccionActualizadaResponse)
def actualizar_direccion(
    direccion_id: Annotated[int, Path(gt=0)],
    data: DireccionEntregaUpdate,
    current_user: Usuario = Depends(get_current_user),
):
    """Actualiza una dirección de entrega (solo si pertenece al usuario autenticado)"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.actualizar_direccion(
                direccion_id, data, usuario_id=current_user.id
            )

            return DireccionActualizadaResponse(
                mensaje="Dirección actualizada exitosamente",
                direccion_id=direccion.id,
                alias=direccion.alias,
                es_principal=direccion.es_principal,
                updated_at=direccion.updated_at,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar dirección: {str(e)}",
        )


# ==================== ENDPOINTS DE CAMBIO DE PRINCIPAL ====================


@router.patch("/{direccion_id}/principal", response_model=DireccionPrincipalResponse)
def marcar_como_principal(
    direccion_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    """Marca una dirección como principal (solo si pertenece al usuario autenticado)"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.marcar_como_principal(
                direccion_id, usuario_id=current_user.id
            )

            return DireccionPrincipalResponse(
                mensaje="Dirección marcada como principal exitosamente",
                direccion_id=direccion.id,
                alias=direccion.alias,
                es_principal=direccion.es_principal,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al marcar como principal: {str(e)}",
        )


# ==================== ENDPOINTS DE ELIMINACIÓN ====================


@router.delete("/{direccion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_direccion(
    direccion_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    """Elimina una dirección (soft delete) — solo si pertenece al usuario autenticado"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            service.eliminar_direccion(direccion_id, usuario_id=current_user.id)
            return None

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al eliminar dirección: {str(e)}",
        )


# ==================== ENDPOINTS DE RESTAURACIÓN ====================


@router.post("/{direccion_id}/restaurar", response_model=DireccionEntregaRead)
def restaurar_direccion(
    direccion_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    """Restaura una dirección eliminada (solo si pertenece al usuario autenticado)"""
    try:
        with DireccionUnitOfWork() as uow:
            service = DireccionEntregaService(uow)
            direccion = service.restaurar_direccion(
                direccion_id, usuario_id=current_user.id
            )
            return direccion

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al restaurar dirección: {str(e)}",
        )
