from datetime import datetime
from typing import Optional

from app.modules.direccion.models import DireccionEntrega
from app.modules.direccion.direccion_uow import DireccionUnitOfWork
from app.modules.direccion.schemas import (
    DireccionEntregaCreate,
    DireccionEntregaUpdate,
    DireccionEntregaCreateCliente,
)


class DireccionEntregaService:
    """Servicio de lógica de negocio para Direcciones de Entrega

    Reglas de negocio:
    - Un usuario solo puede tener UNA dirección principal
    - Si se marca una dirección como principal, las demás se desactivan automáticamente
    - Las direcciones se eliminan de forma lógica (soft delete)
    """

    def __init__(self, uow: DireccionUnitOfWork):
        self.uow = uow

    def crear_direccion(
        self,
        data,
        usuario_id: int,
    ) -> DireccionEntrega:
        """Crea una nueva dirección de entrega para un usuario"""
        cantidad_direcciones = self.uow.direcciones.count_by_usuario(
            usuario_id, include_deleted=False
        )

        # Si es la primera dirección, automáticamente es principal
        es_principal = data.es_principal
        if cantidad_direcciones == 0:
            es_principal = True

        # Si se marca como principal, desactivar otras
        if es_principal:
            self._asegurar_una_principal(usuario_id)

        # Crear la dirección
        direccion = DireccionEntrega(
            usuario_id=usuario_id,
            alias=data.alias,
            calle=data.calle,
            numero=data.numero,
            apartamento=data.apartamento,
            localidad=data.localidad,
            codigo_postal=data.codigo_postal,
            provincia=data.provincia,
            notas=data.notas,
            es_principal=es_principal,
        )

        direccion = self.uow.direcciones.create(direccion)
        self.uow.session.flush()
        self.uow.session.refresh(direccion)

        return direccion

    def obtener_direccion_por_id(
        self, direccion_id: int, include_deleted: bool = False
    ) -> Optional[DireccionEntrega]:
        """Obtiene una dirección por ID"""
        return self.uow.direcciones.get_by_id(
            direccion_id, include_deleted=include_deleted
        )

    def obtener_direcciones_usuario(self, usuario_id: int) -> list[DireccionEntrega]:
        """Obtiene todas las direcciones activas de un usuario"""
        return self.uow.direcciones.get_by_usuario_id(
            usuario_id, include_deleted=False
        )

    def obtener_principal_usuario(
        self, usuario_id: int
    ) -> Optional[DireccionEntrega]:
        """Obtiene la dirección principal de un usuario"""
        return self.uow.direcciones.get_principal_by_usuario(usuario_id)

    def _validar_pertenencia(
        self, direccion_id: int, usuario_id: int, include_deleted: bool = False
    ) -> DireccionEntrega:
        """Valida que una dirección exista y pertenezca al usuario indicado"""
        direccion = self.uow.direcciones.get_by_id(
            direccion_id, include_deleted=include_deleted
        )
        if not direccion:
            raise ValueError(f"Dirección {direccion_id} no encontrada")
        if direccion.usuario_id != usuario_id:
            raise ValueError(f"Dirección {direccion_id} no encontrada")
        return direccion

    def actualizar_direccion(
        self,
        direccion_id: int,
        data: DireccionEntregaUpdate,
        usuario_id: Optional[int] = None,
    ) -> DireccionEntrega:
        """Actualiza una dirección de entrega"""
        if usuario_id is not None:
            direccion = self._validar_pertenencia(direccion_id, usuario_id)
        else:
            direccion = self.uow.direcciones.get_by_id(direccion_id)

        if not direccion:
            raise ValueError(f"Dirección {direccion_id} no encontrada")

        # Si se marca como principal, desactivar otras
        if data.es_principal and not direccion.es_principal:
            self._asegurar_una_principal(
                direccion.usuario_id, exclude_id=direccion_id
            )

        # Construir dict de actualización (solo campos no None)
        update_data = {}
        for field, value in data.dict(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value

        direccion = self.uow.direcciones.update(direccion, update_data)
        self.uow.session.flush()
        self.uow.session.refresh(direccion)

        return direccion

    def marcar_como_principal(
        self, direccion_id: int, usuario_id: Optional[int] = None
    ) -> DireccionEntrega:
        """Marca una dirección como principal y desactiva las demás"""
        if usuario_id is not None:
            direccion = self._validar_pertenencia(direccion_id, usuario_id)
        else:
            direccion = self.uow.direcciones.get_by_id(direccion_id)

        if not direccion:
            raise ValueError(f"Dirección {direccion_id} no encontrada")

        if direccion.is_deleted():
            raise ValueError(
                "No se puede marcar una dirección eliminada como principal"
            )

        # Desactivar otras direcciones principales
        self._asegurar_una_principal(
            direccion.usuario_id, exclude_id=direccion_id
        )

        # Marcar como principal
        direccion.es_principal = True
        direccion = self.uow.direcciones.update(direccion, {"es_principal": True})

        self.uow.session.flush()
        self.uow.session.refresh(direccion)

        return direccion

    def eliminar_direccion(
        self, direccion_id: int, usuario_id: Optional[int] = None
    ) -> DireccionEntrega:
        """Elimina una dirección de forma lógica (soft delete)"""
        if usuario_id is not None:
            direccion = self._validar_pertenencia(direccion_id, usuario_id)
        else:
            direccion = self.uow.direcciones.get_by_id(direccion_id)

        if not direccion:
            raise ValueError(f"Dirección {direccion_id} no encontrada")

        # Si era principal, establecer la siguiente como principal
        era_principal = direccion.es_principal

        direccion = self.uow.direcciones.soft_delete(direccion)

        if era_principal:
            otras = self.uow.direcciones.get_otras_direcciones(
                direccion.usuario_id, exclude_id=direccion_id
            )

            if otras:
                primera = otras[0]
                primera.es_principal = True
                self.uow.direcciones.update(primera, {"es_principal": True})

        self.uow.session.flush()

        return direccion

    def restaurar_direccion(
        self, direccion_id: int, usuario_id: Optional[int] = None
    ) -> DireccionEntrega:
        """Restaura una dirección eliminada (soft delete reversal)"""
        if usuario_id is not None:
            direccion = self._validar_pertenencia(
                direccion_id, usuario_id, include_deleted=True
            )
        else:
            direccion = self.uow.direcciones.get_by_id(
                direccion_id, include_deleted=True
            )

        if not direccion:
            raise ValueError(f"Dirección {direccion_id} no encontrada")

        if not direccion.is_deleted():
            raise ValueError(f"La dirección {direccion_id} no está eliminada")

        direccion.deleted_at = None
        direccion.updated_at = datetime.utcnow()
        self.uow.session.add(direccion)
        self.uow.session.flush()
        self.uow.session.refresh(direccion)

        return direccion

    def _asegurar_una_principal(
        self, usuario_id: int, exclude_id: Optional[int] = None
    ) -> None:
        """Desactiva todas las direcciones principales de un usuario (excepto una)"""
        self.uow.direcciones.desactivar_principal_usuario(
            usuario_id, exclude_id=exclude_id
        )
