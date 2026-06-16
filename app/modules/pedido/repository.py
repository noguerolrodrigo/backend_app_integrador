from datetime import datetime
from typing import Optional

from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.core.base_repository import BaseRepository
from app.modules.pedido.models import (
    Pedido,
    DetallePedido,
    HistorialEstadoPedido,
    EstadoPedido,
)


class PedidoRepository(BaseRepository[Pedido]):
    """Repositorio para operaciones de Pedido"""

    def __init__(self, session: Session):
        super().__init__(Pedido, session)

    def get_by_id(self, pedido_id: int, include_deleted: bool = False) -> Optional[Pedido]:
        """Obtiene un pedido por ID"""
        query = (
            select(Pedido)
            .options(selectinload(Pedido.detalles))
            .where(Pedido.id == pedido_id)
        )
        if not include_deleted:
            query = query.where(Pedido.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_by_numero_pedido(self, numero_pedido: str, include_deleted: bool = False) -> Optional[Pedido]:
        """Obtiene un pedido por número de pedido"""
        query = select(Pedido).where(Pedido.numero_pedido == numero_pedido)
        if not include_deleted:
            query = query.where(Pedido.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_by_usuario_id(self, usuario_id: int, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Pedido]:
        """Obtiene todos los pedidos de un usuario"""
        query = select(Pedido).where(Pedido.usuario_id == usuario_id)
        if not include_deleted:
            query = query.where(Pedido.deleted_at.is_(None))
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def get_all(self, skip: int = 0, limit: int = 100, include_deleted: bool = False) -> list[Pedido]:
        """Obtiene todos los pedidos"""
        query = select(Pedido)
        if not include_deleted:
            query = query.where(Pedido.deleted_at.is_(None))
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def get_by_estado(self, estado: EstadoPedido, skip: int = 0, limit: int = 100) -> list[Pedido]:
        """Obtiene pedidos por estado (solo activos)"""
        query = select(Pedido).where(
            Pedido.estado == estado,
            Pedido.deleted_at.is_(None)
        )
        return self.session.exec(query.offset(skip).limit(limit)).all()

    def create(self, pedido: Pedido) -> Pedido:
        """Crea un nuevo pedido"""
        return self.add(pedido)

    def update(self, pedido: Pedido, data: dict) -> Pedido:
        """Actualiza un pedido"""
        excluded_fields = {"id", "created_at", "deleted_at", "numero_pedido"}
        for key, value in data.items():
            if key not in excluded_fields and value is not None:
                setattr(pedido, key, value)

        pedido.updated_at = datetime.utcnow()
        self.session.add(pedido)
        self.session.flush()
        return pedido

    def soft_delete(self, pedido: Pedido) -> Pedido:
        """Elimina un pedido de forma lógica"""
        pedido.deleted_at = datetime.utcnow()
        pedido.updated_at = datetime.utcnow()
        self.session.add(pedido)
        self.session.flush()
        return pedido

    def exists_numero_pedido(self, numero_pedido: str, exclude_id: Optional[int] = None) -> bool:
        """Verifica si un número de pedido ya existe"""
        query = select(Pedido).where(
            Pedido.numero_pedido == numero_pedido,
            Pedido.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.where(Pedido.id != exclude_id)
        return self.session.exec(query).first() is not None


class DetallePedidoRepository(BaseRepository[DetallePedido]):
    """Repositorio para operaciones de Detalle de Pedido"""

    def __init__(self, session: Session):
        super().__init__(DetallePedido, session)

    def get_by_pedido_id(self, pedido_id: int, include_deleted: bool = False) -> list[DetallePedido]:
        """Obtiene todos los detalles de un pedido"""
        query = select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
        if not include_deleted:
            query = query.where(DetallePedido.deleted_at.is_(None))
        return self.session.exec(query).all()

    def create(self, detalle: DetallePedido) -> DetallePedido:
        """Crea un nuevo detalle de pedido (SNAPSHOT)"""
        return self.add(detalle)

    def create_many(self, detalles: list[DetallePedido]) -> list[DetallePedido]:
        """Crea múltiples detalles de pedido"""
        self.session.add_all(detalles)
        self.session.flush()
        return detalles


class HistorialEstadoPedidoRepository(BaseRepository[HistorialEstadoPedido]):
    """Repositorio para operaciones de Historial de Estado - APPEND-ONLY

    RESTRICCIONES CRÍTICAS:
    - Solo INSERT permitido
    - NO UPDATE
    - NO DELETE
    """

    def __init__(self, session: Session):
        super().__init__(HistorialEstadoPedido, session)

    def get_by_pedido_id(self, pedido_id: int) -> list[HistorialEstadoPedido]:
        """Obtiene el historial de estados de un pedido"""
        query = select(HistorialEstadoPedido).where(
            HistorialEstadoPedido.pedido_id == pedido_id
        ).order_by(HistorialEstadoPedido.created_at.asc())
        return self.session.exec(query).all()

    def get_ultimo_estado(self, pedido_id: int) -> Optional[HistorialEstadoPedido]:
        """Obtiene la última transición de estado (la más reciente)"""
        query = select(HistorialEstadoPedido).where(
            HistorialEstadoPedido.pedido_id == pedido_id
        ).order_by(HistorialEstadoPedido.created_at.desc()).limit(1)
        return self.session.exec(query).first()

    def create(self, historial: HistorialEstadoPedido) -> HistorialEstadoPedido:
        """Crea una nueva entrada en el historial (APPEND-ONLY)

        Este es el ÚNICO método permitido en esta tabla.
        No hay update() ni delete() por diseño de auditoría.
        """
        return self.add(historial)

    def get_transiciones_para_estado(
        self,
        pedido_id: int,
        estado_nuevo: EstadoPedido,
    ) -> list[HistorialEstadoPedido]:
        """Obtiene todos los registros donde el estado_nuevo es el especificado"""
        query = select(HistorialEstadoPedido).where(
            HistorialEstadoPedido.pedido_id == pedido_id,
            HistorialEstadoPedido.estado_nuevo == estado_nuevo,
        ).order_by(HistorialEstadoPedido.created_at.asc())
        return self.session.exec(query).all()

    # Deliberadamente sin implementar: update(), delete()
    # Esto fuerza el patrón append-only
