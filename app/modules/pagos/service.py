import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import mercadopago

from app.core.config import settings
from app.modules.pagos.model import Pago
from app.modules.pagos.pagos_uow import PagoUnitOfWork
from app.modules.pagos.schema import PagoCreate
from app.modules.pedido.models import EstadoPedido, HistorialEstadoPedido, Pedido


def get_mp_sdk() -> mercadopago.SDK:
    return mercadopago.SDK(settings.mp_access_token)


class PagoService:
    def __init__(self, uow: PagoUnitOfWork):
        self.uow = uow

    def crear_pago(self, data: PagoCreate, usuario_id: int) -> Pago:
        pedido = self.uow.session.get(Pedido, data.pedido_id)
        if not pedido:
            raise ValueError(f"Pedido {data.pedido_id} no encontrado")
        if pedido.estado != EstadoPedido.PENDIENTE:
            raise ValueError(
                f"Solo se puede pagar un pedido PENDIENTE (estado actual: {pedido.estado})"
            )

        pago_existente = self.uow.pagos.get_by_pedido_id(data.pedido_id)
        if pago_existente and pago_existente.mp_status == "approved":
            raise ValueError("Este pedido ya tiene un pago aprobado")

        idempotency_key = str(uuid.uuid4())
        external_reference = str(data.pedido_id)

        sdk = get_mp_sdk()
        mp_response = sdk.payment().create(
            {
                "transaction_amount": float(pedido.monto_total),
                "token": data.token,
                "description": f"Pedido {pedido.numero_pedido}",
                "installments": data.installments,
                "payment_method_id": data.payment_method_id,
                "issuer_id": data.issuer_id,
                "external_reference": external_reference,
                "notification_url": settings.mp_notification_url,
            },
            {"X-Idempotency-Key": idempotency_key},
        )

        response_body = mp_response.get("response", {})
        mp_status = response_body.get("status", "pending")

        pago = Pago(
            pedido_id=data.pedido_id,
            mp_payment_id=response_body.get("id"),
            mp_status=mp_status,
            mp_status_detail=response_body.get("status_detail"),
            transaction_amount=Decimal(str(response_body.get("transaction_amount", pedido.monto_total))),
            payment_method_id=response_body.get("payment_method_id", data.payment_method_id),
            external_reference=external_reference,
            idempotency_key=idempotency_key,
        )
        self.uow.pagos.add(pago)

        if mp_status == "approved":
            self._confirmar_pedido(pedido)

        return pago

    def procesar_webhook(
        self, payload: dict
    ) -> Optional[tuple[Pago, int, Optional[EstadoPedido]]]:
        if payload.get("type") != "payment":
            return None

        payment_id = int(payload["data"]["id"])

        sdk = get_mp_sdk()
        mp_response = sdk.payment().get(payment_id)
        response_body = mp_response.get("response", {})

        mp_status = response_body.get("status")
        mp_status_detail = response_body.get("status_detail")
        payment_method_id = response_body.get("payment_method_id")
        external_reference = response_body.get("external_reference")

        if not external_reference:
            return None

        pago = self.uow.pagos.get_by_external_reference(external_reference)
        if not pago:
            return None

        pedido_id = int(external_reference)
        estado_anterior = None

        pago.mp_payment_id = payment_id
        pago.mp_status = mp_status
        pago.mp_status_detail = mp_status_detail
        pago.payment_method_id = payment_method_id
        pago.updated_at = datetime.utcnow()
        self.uow.session.add(pago)
        self.uow.session.flush()

        if mp_status == "approved":
            pedido = self.uow.session.get(Pedido, pedido_id)
            if pedido and pedido.estado == EstadoPedido.PENDIENTE:
                estado_anterior = EstadoPedido.PENDIENTE
                self._confirmar_pedido(pedido)

        return (pago, pedido_id, estado_anterior)

    def obtener_pago(self, pedido_id: int) -> Optional[Pago]:
        return self.uow.pagos.get_by_pedido_id(pedido_id)

    def _confirmar_pedido(self, pedido: Pedido) -> None:
        pedido.estado = EstadoPedido.CONFIRMADO
        pedido.updated_at = datetime.utcnow()
        historial = HistorialEstadoPedido(
            pedido_id=pedido.id,
            usuario_id=None,
            estado_anterior=EstadoPedido.PENDIENTE,
            estado_nuevo=EstadoPedido.CONFIRMADO,
            razon="Pago confirmado por MercadoPago",
        )
        self.uow.session.add(pedido)
        self.uow.session.add(historial)
        self.uow.session.flush()
