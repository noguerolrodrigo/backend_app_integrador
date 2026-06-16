from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func

if TYPE_CHECKING:
    from app.modules.usuario.models import Usuario
    from app.modules.producto.model import Producto


class EstadoPedido(str, Enum):
    """Estados posibles de un pedido"""
    PENDIENTE = "PENDIENTE"
    CONFIRMADO = "CONFIRMADO"
    EN_PREPARACION = "EN_PREPARACION"
    EN_CAMINO = "EN_CAMINO"
    ENTREGADO = "ENTREGADO"
    CANCELADO = "CANCELADO"


class FormaPago(str, Enum):
    """Formas de pago disponibles"""
    TARJETA_CREDITO = "TARJETA_CREDITO"
    TARJETA_DEBITO = "TARJETA_DEBITO"
    EFECTIVO = "EFECTIVO"
    TRANSFERENCIA = "TRANSFERENCIA"
    MERCADO_PAGO = "MERCADO_PAGO"


class Pedido(SQLModel, table=True):
    """Modelo de Pedido - Registra la información principal del pedido"""
    __tablename__ = "pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    usuario_id: int = Field(foreign_key="usuario.id", nullable=False, index=True)
    
    numero_pedido: str = Field(
        max_length=50, 
        unique=True, 
        index=True,
        nullable=False,
        description="Número único de pedido (ej: PED-2024-001)"
    )
    
    # Estado actual del pedido
    estado: EstadoPedido = Field(
        default=EstadoPedido.PENDIENTE,
        nullable=False,
        index=True,
        description="Estado actual del pedido"
    )
    
    # Datos de pago
    forma_pago: FormaPago = Field(nullable=False)
    monto_total: float = Field(ge=0, nullable=False)
    
    # Direcciones
    direccion_entrega: str = Field(max_length=500, nullable=False)
    observaciones: Optional[str] = Field(max_length=1000, default=None)
    
    # Timestamps y auditoría
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relaciones
    detalles: List["DetallePedido"] = Relationship(
        back_populates="pedido",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    historial_estado: List["HistorialEstadoPedido"] = Relationship(
        back_populates="pedido",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    
    usuario: "Usuario" = Relationship()

    def is_deleted(self) -> bool:
        """Verifica si el pedido está eliminado"""
        return self.deleted_at is not None

    def puede_cancelarse(self) -> bool:
        """Verifica si el pedido puede ser cancelado"""
        return self.estado in [EstadoPedido.PENDIENTE, EstadoPedido.CONFIRMADO]

    def monto_total_detalles(self) -> float:
        """Calcula el monto total desde los detalles"""
        return sum(d.subtotal for d in self.detalles) if self.detalles else 0.0


class DetallePedido(SQLModel, table=True):
    """Modelo de Detalle de Pedido - Snapshot del producto en el momento de la compra"""
    __tablename__ = "detalle_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, index=True)
    producto_id: int = Field(foreign_key="producto.id", nullable=False, index=True)
    
    # SNAPSHOT PATTERN: Valores copiados del producto en el momento de la compra
    # Estos valores NUNCA cambiarán, aunque el producto original se modifique
    nombre_producto: str = Field(
        max_length=150,
        nullable=False,
        description="Nombre del producto SNAPSHOT (inmutable)"
    )
    precio_unitario: float = Field(
        ge=0,
        nullable=False,
        description="Precio unitario SNAPSHOT (inmutable)"
    )
    cantidad: int = Field(ge=1, nullable=False)
    
    # Campos calculados (derivados)
    subtotal: float = Field(
        nullable=False,
        description="Subtotal = precio_unitario * cantidad"
    )
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    deleted_at: Optional[datetime] = Field(default=None, nullable=True)
    
    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="detalles")

    def is_deleted(self) -> bool:
        """Verifica si el detalle está eliminado"""
        return self.deleted_at is not None


class HistorialEstadoPedido(SQLModel, table=True):
    """Modelo de Historial de Estado - APPEND-ONLY, jamás se actualiza o elimina
    
    Este modelo registra cada transición de estado del pedido.
    Es crítico para auditoría y trazabilidad.
    
    Restricciones:
    - SOLO INSERT
    - NUNCA UPDATE
    - NUNCA DELETE
    """
    __tablename__ = "historial_estado_pedido"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    pedido_id: int = Field(foreign_key="pedido.id", nullable=False, index=True)
    usuario_id: Optional[int] = Field(foreign_key="usuario.id", nullable=True)
    
    estado_anterior: Optional[EstadoPedido] = Field(
        nullable=True,
        description="Estado anterior (None en el primer registro)"
    )
    estado_nuevo: EstadoPedido = Field(
        nullable=False,
        description="Estado nuevo (la transición)"
    )
    
    razon: Optional[str] = Field(
        max_length=500,
        default=None,
        description="Razón del cambio de estado (ej: 'Cliente canceló por cambio de opinión')"
    )
    
    # Timestamp de la transición (APPEND-ONLY)
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
        description="Momento EXACTO de la transición"
    )
    
    # Relaciones
    pedido: "Pedido" = Relationship(back_populates="historial_estado")

    def __repr__(self) -> str:
        return f"HistorialEstadoPedido(pedido_id={self.pedido_id}, {self.estado_anterior} -> {self.estado_nuevo} at {self.created_at})"
