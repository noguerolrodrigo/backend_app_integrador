from datetime import date
from decimal import Decimal

from app.modules.estadisticas.estadisticas_uow import EstadisticasUnitOfWork
from app.modules.estadisticas.schemas import (
    IngresosFormaPagoItem,
    IngresosResponse,
    PedidosEstadoItem,
    ProductoTopItem,
    ResumenResponse,
    VentasPeriodoItem,
)


def _to_decimal(value) -> Decimal:
    # EST-04: nunca float nativo para dinero
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(Decimal("0.01"))


def get_ventas_periodo(
    uow: EstadisticasUnitOfWork,
    desde: date,
    hasta: date,
    agrupacion: str,
) -> list[VentasPeriodoItem]:
    rows = uow.repo.get_ventas_periodo(desde, hasta, agrupacion)
    return [
        VentasPeriodoItem(
            periodo=str(row.periodo),
            total_ventas=_to_decimal(row.total_ventas),
            cantidad_pedidos=row.cantidad_pedidos,
        )
        for row in rows
    ]


def get_productos_top(uow: EstadisticasUnitOfWork, limit: int) -> list[ProductoTopItem]:
    rows = uow.repo.get_productos_top(limit)
    return [
        ProductoTopItem(
            producto_id=row.producto_id,
            nombre=row.nombre,
            total_ingresos=_to_decimal(row.total_ingresos),
            cantidad_vendida=int(row.cantidad_vendida),
        )
        for row in rows
    ]


def get_pedidos_por_estado(uow: EstadisticasUnitOfWork) -> list[PedidosEstadoItem]:
    rows = uow.repo.get_pedidos_por_estado()
    return [
        PedidosEstadoItem(
            estado=str(row.estado.value) if hasattr(row.estado, "value") else str(row.estado),
            cantidad=row.cantidad,
        )
        for row in rows
    ]


def get_ingresos(
    uow: EstadisticasUnitOfWork,
    desde: date,
    hasta: date,
) -> IngresosResponse:
    rows = uow.repo.get_ingresos_por_forma_pago(desde, hasta)
    items = [
        IngresosFormaPagoItem(
            forma_pago=str(row.forma_pago.value) if hasattr(row.forma_pago, "value") else str(row.forma_pago),
            total=_to_decimal(row.total),
            cantidad_pagos=row.cantidad_pagos,
        )
        for row in rows
    ]
    return IngresosResponse(desde=desde, hasta=hasta, items=items)


def get_resumen(uow: EstadisticasUnitOfWork) -> ResumenResponse:
    kpis = uow.repo.get_resumen_kpis()
    return ResumenResponse(
        ventas_hoy=_to_decimal(kpis["ventas_hoy"]),
        ticket_promedio=_to_decimal(kpis["ticket_promedio"]),
        pedidos_activos=int(kpis["pedidos_activos"] or 0),
        ventas_mes_actual=_to_decimal(kpis["ventas_mes_actual"]),
    )
