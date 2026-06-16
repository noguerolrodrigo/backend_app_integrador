from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from app.core.deps import get_current_user, require_role
from app.core.ws_manager import ws_manager
from app.modules.pagos.pagos_uow import PagoUnitOfWork
from app.modules.pagos.schema import PagoCreate, PagoRead
from app.modules.pagos.service import PagoService
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/api/v1/pagos", tags=["Pagos"])


@router.post("/crear", response_model=PagoRead, status_code=status.HTTP_201_CREATED)
async def crear_pago(
    data: PagoCreate,
    current_user: Usuario = Depends(require_role(["CLIENT", "ADMIN"])),
):
    try:
        with PagoUnitOfWork() as uow:
            service = PagoService(uow)
            pago = service.crear_pago(data, current_user.id)
            pid = pago.pedido_id
            mp_status = pago.mp_status
            response = PagoRead.model_validate(pago)

        # RN-06: broadcast DESPUÉS del commit del UoW
        if mp_status == "approved":
            await ws_manager.broadcast_pedido(pid, {
                "event": "pago_confirmado",
                "pedido_id": pid,
                "estado_anterior": "PENDIENTE",
                "estado_nuevo": "CONFIRMADO",
                "usuario_id": current_user.id,
                "motivo": None,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })

        return response

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def webhook(request: Request):
    body = await request.json()
    result = None
    mp_status = None

    try:
        with PagoUnitOfWork() as uow:
            service = PagoService(uow)
            result = service.procesar_webhook(body)
            if result:
                pago, pedido_id, estado_anterior = result
                mp_status = pago.mp_status

        # RN-06: broadcast DESPUÉS del commit del UoW
        if result and mp_status == "approved":
            _, pedido_id, estado_anterior = result
            await ws_manager.broadcast_pedido(pedido_id, {
                "event": "pago_confirmado",
                "pedido_id": pedido_id,
                "estado_anterior": estado_anterior.value if estado_anterior else None,
                "estado_nuevo": "CONFIRMADO",
                "usuario_id": None,
                "motivo": None,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
    except Exception:
        pass  # Webhooks siempre retornan 200 para evitar reintentos de MP

    return {"status": "ok"}


@router.get("/{pedido_id}", response_model=PagoRead)
def obtener_pago(
    pedido_id: Annotated[int, Path(gt=0)],
    current_user: Usuario = Depends(get_current_user),
):
    with PagoUnitOfWork() as uow:
        service = PagoService(uow)
        pago = service.obtener_pago(pedido_id)

        if not pago:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado para este pedido",
            )

        user_roles = {r.codigo for r in current_user.roles}
        if "ADMIN" not in user_roles and pago.pedido.usuario_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Sin permisos para ver este pago",
            )

        return PagoRead.model_validate(pago)
