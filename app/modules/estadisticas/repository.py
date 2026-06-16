from datetime import date
from decimal import Decimal

from sqlalchemy import func, cast, Date
from sqlmodel import Session, select

from app.modules.pedido.models import DetallePedido, EstadoPedido, Pedido
from app.modules.pagos.model import Pago

_AGRUPACIONES_VALIDAS = {"day", "week", "month"}


class EstadisticasRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_ventas_periodo(self, desde: date, hasta: date, agrupacion: str):
        if agrupacion not in _AGRUPACIONES_VALIDAS:
            raise ValueError(f"agrupacion debe ser uno de: {_AGRUPACIONES_VALIDAS}")

        periodo_col = func.date_trunc(agrupacion, Pedido.created_at).label("periodo")
        stmt = (
            select(
                periodo_col,
                func.coalesce(func.sum(Pedido.monto_total), 0).label("total_ventas"),
                func.count(Pedido.id).label("cantidad_pedidos"),
            )
            .where(Pedido.estado != EstadoPedido.CANCELADO)
            .where(cast(Pedido.created_at, Date).between(desde, hasta))
            .group_by(periodo_col)
            .order_by(periodo_col)
        )
        return self.session.execute(stmt).all()

    def get_productos_top(self, limit: int):
        # EST-02: usa subtotal de DetallePedido (snapshot inmutable)
        stmt = (
            select(
                DetallePedido.producto_id,
                DetallePedido.nombre_producto.label("nombre"),
                func.coalesce(func.sum(DetallePedido.subtotal), 0).label("total_ingresos"),
                func.coalesce(func.sum(DetallePedido.cantidad), 0).label("cantidad_vendida"),
            )
            .join(Pedido, DetallePedido.pedido_id == Pedido.id)
            .where(Pedido.estado != EstadoPedido.CANCELADO)
            .group_by(DetallePedido.producto_id, DetallePedido.nombre_producto)
            .order_by(func.sum(DetallePedido.subtotal).desc())
            .limit(limit)
        )
        return self.session.execute(stmt).all()

    def get_pedidos_por_estado(self):
        stmt = (
            select(
                Pedido.estado.label("estado"),
                func.count(Pedido.id).label("cantidad"),
            )
            .group_by(Pedido.estado)
            .order_by(func.count(Pedido.id).desc())
        )
        return self.session.execute(stmt).all()

    def get_ingresos_por_forma_pago(self, desde: date, hasta: date):
        # EST-03: solo pagos mp_status='approved'
        stmt = (
            select(
                Pedido.forma_pago.label("forma_pago"),
                func.coalesce(func.sum(Pago.transaction_amount), 0).label("total"),
                func.count(Pago.id).label("cantidad_pagos"),
            )
            .join(Pago, Pago.pedido_id == Pedido.id)
            .where(Pago.mp_status == "approved")
            .where(cast(func.timezone('UTC', Pedido.created_at), Date).between(desde, hasta))
            .group_by(Pedido.forma_pago)
        )
        return self.session.execute(stmt).all()

    def get_resumen_kpis(self) -> dict:
        from datetime import datetime

        today = datetime.utcnow().date()
        mes_inicio = today.replace(day=1)

        # Ventas hoy (EST-01: excluir CANCELADO)
        ventas_hoy = self.session.execute(
            select(func.coalesce(func.sum(Pedido.monto_total), 0))
            .where(Pedido.estado != EstadoPedido.CANCELADO)
            .where(cast(Pedido.created_at, Date) == today)
        ).scalar()

        # Ticket promedio (EST-01)
        ticket_promedio = self.session.execute(
            select(func.coalesce(func.avg(Pedido.monto_total), 0))
            .where(Pedido.estado != EstadoPedido.CANCELADO)
        ).scalar()

        # Pedidos activos (ni ENTREGADO ni CANCELADO)
        pedidos_activos = self.session.execute(
            select(func.count(Pedido.id))
            .where(Pedido.estado.not_in([EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]))
        ).scalar()

        # Ventas mes actual (EST-01, EST-05)
        ventas_mes = self.session.execute(
            select(func.coalesce(func.sum(Pedido.monto_total), 0))
            .where(Pedido.estado != EstadoPedido.CANCELADO)
            .where(cast(Pedido.created_at, Date).between(mes_inicio, today))
        ).scalar()

        return {
            "ventas_hoy": ventas_hoy,
            "ticket_promedio": ticket_promedio,
            "pedidos_activos": pedidos_activos,
            "ventas_mes_actual": ventas_mes,
        }
