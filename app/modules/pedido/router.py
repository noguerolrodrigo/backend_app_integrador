from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_current_user, require_role
from app.core.ws_manager import ws_manager
from app.modules.pedido.service import PedidoService
from app.modules.pedido.pedido_uow import PedidoUnitOfWork
from app.modules.usuario.models import Usuario
from app.modules.pedido.models import EstadoPedido
from app.modules.pedido.schemas import (
    PedidoCreate,
    PedidoRead,
    PedidoReadSimple,
    PedidoReadConDetalles,
    PedidoCambiarEstado,
    PedidoCreatedResponse,
    EstadoCambiadoResponse,
    HistorialEstadoPedidoRead,
)

router = APIRouter(prefix="/api/v1/pedidos", tags=["Pedidos"])


# ==================== ENDPOINTS DE CREACIÓN ====================


@router.post("/", response_model=PedidoCreatedResponse, status_code=status.HTTP_201_CREATED)
def crear_pedido(
    data: PedidoCreate,
):
    """Crea un nuevo pedido (UNIT OF WORK)"""
    try:
        with PedidoUnitOfWork() as uow:
            service = PedidoService(uow)
            pedido = service.crear_pedido(
                usuario_id=data.usuario_id,
                forma_pago=data.forma_pago,
                direccion_entrega=data.direccion_entrega,
                detalles_data=data.detalles,
                observaciones=data.observaciones,
            )

            return PedidoCreatedResponse(
                mensaje="Pedido creado exitosamente",
                pedido_id=pedido.id,
                numero_pedido=pedido.numero_pedido,
                monto_total=pedido.monto_total,
                estado=pedido.estado,
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear pedido: {str(e)}",
        )


# ==================== ENDPOINTS DE LECTURA ====================


@router.get("/", response_model=list[PedidoReadSimple])
def listar_pedidos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    estado: Annotated[Optional[EstadoPedido], Query()] = None,
    _: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Lista todos los pedidos (con filtro opcional por estado)"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        if estado:
            return service.listar_por_estado(estado, skip, limit)
        return service.listar_pedidos(skip, limit)


@router.get("/usuario/{usuario_id}", response_model=list[PedidoReadSimple])
def listar_pedidos_usuario(
    usuario_id: Annotated[int, Path(gt=0)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    _: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Lista todos los pedidos de un usuario específico"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        return service.listar_pedidos_usuario(usuario_id, skip, limit)


@router.get("/{pedido_id}/historial", response_model=list[HistorialEstadoPedidoRead])
def obtener_historial_estado(
    pedido_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Obtiene el historial completo de transiciones de un pedido (AUDIT TRAIL)"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        pedido = service.obtener_pedido_por_id(pedido_id)

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {pedido_id} no encontrado",
            )

        return service.obtener_historial_estado(pedido_id)


@router.get("/numero/{numero_pedido}", response_model=PedidoReadConDetalles)
def obtener_por_numero_pedido(
    numero_pedido: Annotated[str, Path(min_length=1)],
    _: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Obtiene un pedido por su número único"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        pedido = service.obtener_pedido_por_numero(numero_pedido)

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {numero_pedido} no encontrado",
            )

        return pedido


# ==================== ENDPOINTS DE CAMBIO DE ESTADO ====================


@router.patch("/{pedido_id}/estado", response_model=EstadoCambiadoResponse)
async def cambiar_estado_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    data: PedidoCambiarEstado,
    current_user: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Cambia el estado de un pedido (APPEND-ONLY AUDIT TRAIL). Broadcast WS post-commit (RN-06)."""
    try:
        with PedidoUnitOfWork() as uow:
            service = PedidoService(uow)
            pedido = service.cambiar_estado(
                pedido_id=pedido_id,
                estado_nuevo=data.estado_nuevo,
                razon=data.razon,
                usuario_id=current_user.id,
            )

            historial = service.obtener_historial_estado(pedido_id)
            estado_anterior = (
                historial[-2].estado_nuevo
                if len(historial) > 1
                else EstadoPedido.PENDIENTE
            )

            # Extraer escalares dentro del with antes de que el session cierre
            pid = pedido.id
            est_nuevo_val = pedido.estado
            response = EstadoCambiadoResponse(
                mensaje=f"Estado actualizado a {data.estado_nuevo}",
                pedido_id=pid,
                numero_pedido=pedido.numero_pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=est_nuevo_val,
                fecha_cambio=pedido.updated_at,
            )

        # --- UoW committea al salir del with --- RN-06: broadcast DESPUÉS del commit ---
        await ws_manager.broadcast_pedido(pid, {
            "event": "estado_cambiado",
            "pedido_id": pid,
            "estado_anterior": estado_anterior.value if estado_anterior else None,
            "estado_nuevo": est_nuevo_val.value,
            "usuario_id": current_user.id,
            "motivo": data.razon,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{pedido_id}/cancelar", response_model=EstadoCambiadoResponse)
async def cancelar_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    razon: Annotated[Optional[str], Query()] = None,
    current_user: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Cancela un pedido (solo si está en PENDIENTE o CONFIRMADO). Broadcast WS post-commit (RN-06)."""
    try:
        with PedidoUnitOfWork() as uow:
            service = PedidoService(uow)
            pedido = service.cancelar_pedido(pedido_id, razon)

            historial = service.obtener_historial_estado(pedido_id)
            estado_anterior = (
                historial[-2].estado_nuevo
                if len(historial) > 1
                else EstadoPedido.PENDIENTE
            )

            pid = pedido.id
            response = EstadoCambiadoResponse(
                mensaje="Pedido cancelado exitosamente",
                pedido_id=pid,
                numero_pedido=pedido.numero_pedido,
                estado_anterior=estado_anterior,
                estado_nuevo=pedido.estado,
                fecha_cambio=pedido.updated_at,
            )

        # --- RN-06: broadcast DESPUÉS del commit ---
        await ws_manager.broadcast_pedido(pid, {
            "event": "pedido_cancelado",
            "pedido_id": pid,
            "estado_anterior": estado_anterior.value if estado_anterior else None,
            "estado_nuevo": "CANCELADO",
            "usuario_id": current_user.id,
            "motivo": razon,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        return response

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


# ==================== ENDPOINTS PARA CLIENTES (STORE-APP) ====================


@router.get("/mis-pedidos", response_model=list[PedidoReadSimple])
def listar_mis_pedidos(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    current_user: Usuario = Depends(get_current_user),
):
    """Devuelve los pedidos del usuario autenticado (para store-app, role CLIENT)"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        return service.listar_pedidos_usuario(current_user.id, skip, limit)


@router.get("/{pedido_id}", response_model=PedidoReadConDetalles)
def obtener_pedido(
    pedido_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    """Obtiene un pedido por ID (solo si es del usuario o ADMIN/PEDIDOS)"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        pedido = service.obtener_pedido_por_id(pedido_id)

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {pedido_id} no encontrado",
            )

        # Permitir si es CLIENT y el pedido es suyo, o si tiene rol ADMIN/PEDIDOS
        user_roles = {r.codigo for r in current_user.roles}
        is_staff = bool(user_roles & {"ADMIN", "PEDIDOS"})

        if not is_staff and pedido.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver este pedido",
            )

        return pedido


# ==================== ENDPOINTS DE VALIDACIÓN ====================


@router.get("/{pedido_id}/puede-cancelarse")
def puede_cancelarse(
    pedido_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN", "PEDIDOS"])),
):
    """Verifica si un pedido puede ser cancelado"""
    with PedidoUnitOfWork() as uow:
        service = PedidoService(uow)
        pedido = service.obtener_pedido_por_id(pedido_id)

        if not pedido:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pedido {pedido_id} no encontrado",
            )

        puede = pedido.puede_cancelarse()

        return {
            "puede_cancelarse": puede,
            "estado_actual": pedido.estado,
            "mensaje": "Sí puede cancelarse" if puede else f"No puede cancelarse (estado: {pedido.estado})",
        }
