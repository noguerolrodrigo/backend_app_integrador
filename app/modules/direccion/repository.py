from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.core.base_repository import BaseRepository
from app.modules.direccion.models import DireccionEntrega


class DireccionEntregaRepository(BaseRepository[DireccionEntrega]):
    """Repositorio para operaciones de Dirección de Entrega"""

    def __init__(self, session: Session):
        super().__init__(DireccionEntrega, session)

    def get_by_id(
        self,
        direccion_id: int,
        include_deleted: bool = False,
    ) -> Optional[DireccionEntrega]:
        """Obtiene una dirección por ID"""
        query = select(DireccionEntrega).where(DireccionEntrega.id == direccion_id)
        if not include_deleted:
            query = query.where(DireccionEntrega.deleted_at.is_(None))
        return self.session.exec(query).first()

    def get_by_usuario_id(
        self,
        usuario_id: int,
        include_deleted: bool = False,
    ) -> list[DireccionEntrega]:
        """Obtiene todas las direcciones de un usuario"""
        query = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id
        )
        if not include_deleted:
            query = query.where(DireccionEntrega.deleted_at.is_(None))
        query = query.order_by(DireccionEntrega.es_principal.desc(), DireccionEntrega.created_at.desc())
        return self.session.exec(query).all()

    def get_principal_by_usuario(self, usuario_id: int) -> Optional[DireccionEntrega]:
        """Obtiene la dirección principal de un usuario"""
        query = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.es_principal == True,
            DireccionEntrega.deleted_at.is_(None)
        )
        return self.session.exec(query).first()

    def get_otras_direcciones(
        self,
        usuario_id: int,
        exclude_id: Optional[int] = None,
    ) -> list[DireccionEntrega]:
        """Obtiene todas las direcciones de un usuario excepto la principal (y opcionalmente una específica)"""
        query = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.es_principal == False,
            DireccionEntrega.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.where(DireccionEntrega.id != exclude_id)
        return self.session.exec(query).all()

    def create(self, direccion: DireccionEntrega) -> DireccionEntrega:
        """Crea una nueva dirección"""
        return self.add(direccion)

    def update(self, direccion: DireccionEntrega, data: dict) -> DireccionEntrega:
        """Actualiza una dirección"""
        excluded_fields = {"id", "created_at", "deleted_at", "usuario_id"}
        for key, value in data.items():
            if key not in excluded_fields and value is not None:
                setattr(direccion, key, value)

        direccion.updated_at = datetime.utcnow()
        self.session.add(direccion)
        self.session.flush()
        return direccion

    def soft_delete(self, direccion: DireccionEntrega) -> DireccionEntrega:
        """Elimina una dirección de forma lógica"""
        direccion.deleted_at = datetime.utcnow()
        direccion.updated_at = datetime.utcnow()
        self.session.add(direccion)
        self.session.flush()
        return direccion

    def desactivar_principal_usuario(self, usuario_id: int, exclude_id: Optional[int] = None) -> None:
        """Desactiva la dirección principal de un usuario (marca es_principal=False)

        Útil cuando se establece una nueva dirección como principal.
        """
        query = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id,
            DireccionEntrega.es_principal == True,
            DireccionEntrega.deleted_at.is_(None)
        )
        if exclude_id:
            query = query.where(DireccionEntrega.id != exclude_id)

        direcciones = self.session.exec(query).all()
        for direccion in direcciones:
            direccion.es_principal = False
            direccion.updated_at = datetime.utcnow()
            self.session.add(direccion)

    def count_by_usuario(self, usuario_id: int, include_deleted: bool = False) -> int:
        """Cuenta cuántas direcciones tiene un usuario"""
        query = select(DireccionEntrega).where(
            DireccionEntrega.usuario_id == usuario_id
        )
        if not include_deleted:
            query = query.where(DireccionEntrega.deleted_at.is_(None))
        return len(self.session.exec(query).all())
