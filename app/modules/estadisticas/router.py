from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import require_role
from app.modules.estadisticas import service
from app.modules.estadisticas.estadisticas_uow import EstadisticasUnitOfWork
from app.modules.estadisticas.schemas import (
    IngresosResponse,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)

router = APIRouter(prefix="/api/v1/estadisticas", tags=["Estadísticas"])


@router.get("/ventas", response_model=list[VentasPeriodoItem])
def ventas_periodo(
    desde: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    agrupacion: str = Query("day", description="Agrupación: day, week, month"),
    _=Depends(require_role(["ADMIN"])),
):
    try:
        with EstadisticasUnitOfWork() as uow:
            return service.get_ventas_periodo(uow, desde, hasta, agrupacion)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/productos-top", response_model=list[ProductoTopItem])
def productos_top(
    limit: int = Query(10, ge=1, le=50, description="Número máximo de productos"),
    _=Depends(require_role(["ADMIN"])),
):
    with EstadisticasUnitOfWork() as uow:
        return service.get_productos_top(uow, limit)


@router.get("/pedidos-por-estado", response_model=list[PedidosEstadoItem])
def pedidos_por_estado(_=Depends(require_role(["ADMIN"]))):
    with EstadisticasUnitOfWork() as uow:
        return service.get_pedidos_por_estado(uow)


@router.get("/ingresos", response_model=IngresosResponse)
def ingresos(
    desde: date = Query(..., description="Fecha inicio (YYYY-MM-DD)"),
    hasta: date = Query(..., description="Fecha fin (YYYY-MM-DD)"),
    _=Depends(require_role(["ADMIN"])),
):
    with EstadisticasUnitOfWork() as uow:
        return service.get_ingresos(uow, desde, hasta)


@router.get("/resumen", response_model=ResumenResponse)
def resumen(_=Depends(require_role(["ADMIN"]))):
    with EstadisticasUnitOfWork() as uow:
        return service.get_resumen(uow)
