from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel


class VentasPeriodoItem(SQLModel):
    periodo: str
    total_ventas: Decimal
    cantidad_pedidos: int


class ProductoTopItem(SQLModel):
    producto_id: int
    nombre: str
    total_ingresos: Decimal
    cantidad_vendida: int


class PedidosEstadoItem(SQLModel):
    estado: str
    cantidad: int


class IngresosFormaPagoItem(SQLModel):
    forma_pago: str
    total: Decimal
    cantidad_pagos: int


class IngresosResponse(SQLModel):
    desde: date
    hasta: date
    items: list[IngresosFormaPagoItem]


class ResumenResponse(SQLModel):
    ventas_hoy: Decimal
    ticket_promedio: Decimal
    pedidos_activos: int
    ventas_mes_actual: Decimal
