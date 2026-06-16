from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel

from app.modules.pedido.models import EstadoPedido, FormaPago


# ==================== SCHEMAS DE FORMA DE PAGO ====================

class FormaPagoRead(SQLModel):
    """Schema para lectura de forma de pago"""
    valor: str
    descripcion: str


# ==================== SCHEMAS DE DETALLE PEDIDO ====================

class DetallePedidoCreate(SQLModel):
    """Schema para crear detalle de pedido"""
    producto_id: int
    cantidad: int
    # Los campos nombre_producto y precio_unitario se copian del Producto


class DetallePedidoRead(SQLModel):
    """Schema para leer detalle de pedido"""
    id: int
    pedido_id: int
    producto_id: int
    
    # SNAPSHOT PATTERN
    nombre_producto: str
    precio_unitario: float
    cantidad: int
    subtotal: float
    
    created_at: datetime
    deleted_at: Optional[datetime]


# ==================== SCHEMAS DE HISTORIAL ESTADO ====================

class HistorialEstadoPedidoRead(SQLModel):
    """Schema para leer entrada del historial de estados"""
    id: int
    pedido_id: int
    usuario_id: Optional[int]
    
    estado_anterior: Optional[EstadoPedido]
    estado_nuevo: EstadoPedido
    razon: Optional[str]
    
    created_at: datetime


# ==================== SCHEMAS DE PEDIDO ====================

class PedidoCreate(SQLModel):
    """Schema para crear un nuevo pedido"""
    usuario_id: int
    forma_pago: FormaPago
    direccion_entrega: str
    observaciones: Optional[str] = None
    
    # Detalles del pedido (productos a comprar)
    detalles: List[DetallePedidoCreate]


class PedidoUpdate(SQLModel):
    """Schema para actualizar un pedido"""
    forma_pago: Optional[FormaPago] = None
    direccion_entrega: Optional[str] = None
    observaciones: Optional[str] = None


class PedidoCambiarEstado(SQLModel):
    """Schema para cambiar estado de pedido"""
    estado_nuevo: EstadoPedido
    razon: Optional[str] = None


class PedidoRead(SQLModel):
    """Schema para leer un pedido completo"""
    id: int
    numero_pedido: str
    usuario_id: int
    
    estado: EstadoPedido
    forma_pago: FormaPago
    monto_total: float
    
    direccion_entrega: str
    observaciones: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime]
    
    # Relaciones
    detalles: List[DetallePedidoRead] = []
    historial_estado: List[HistorialEstadoPedidoRead] = []


class PedidoReadSimple(SQLModel):
    """Schema simplificado para listados"""
    id: int
    numero_pedido: str
    usuario_id: int
    estado: EstadoPedido
    monto_total: float
    created_at: datetime


class PedidoReadConDetalles(SQLModel):
    """Schema para leer pedido con detalles (sin historial completo)"""
    id: int
    numero_pedido: str
    usuario_id: int
    
    estado: EstadoPedido
    forma_pago: FormaPago
    monto_total: float
    
    direccion_entrega: str
    observaciones: Optional[str]
    
    created_at: datetime
    updated_at: datetime
    
    detalles: List[DetallePedidoRead] = []


# ==================== SCHEMAS DE RESPUESTA ====================

class PedidoCreatedResponse(SQLModel):
    """Response al crear un pedido exitosamente"""
    mensaje: str
    pedido_id: int
    numero_pedido: str
    monto_total: float
    estado: EstadoPedido


class EstadoCambiadoResponse(SQLModel):
    """Response al cambiar estado de pedido"""
    mensaje: str
    pedido_id: int
    numero_pedido: str
    estado_anterior: EstadoPedido
    estado_nuevo: EstadoPedido
    fecha_cambio: datetime
