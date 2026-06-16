from sqlmodel import select

from app.modules.unidad_medida.model import UnidadMedida
from app.modules.unidad_medida.unidad_medida_uow import UnidadMedidaUnitOfWork


def create(uow: UnidadMedidaUnitOfWork, data) -> UnidadMedida:
    unidad = UnidadMedida(**data.model_dump())
    uow.session.add(unidad)
    uow.session.flush()
    uow.session.refresh(unidad)
    return unidad


def get_all(uow: UnidadMedidaUnitOfWork, limit: int) -> list[UnidadMedida]:
    return list(uow.session.exec(select(UnidadMedida).limit(limit)).all())


def get_by_id(uow: UnidadMedidaUnitOfWork, unidad_id: int) -> UnidadMedida | None:
    return uow.session.get(UnidadMedida, unidad_id)


def update(uow: UnidadMedidaUnitOfWork, unidad_id: int, data_dict: dict) -> UnidadMedida | None:
    unidad = uow.session.get(UnidadMedida, unidad_id)
    if not unidad:
        return None
    for key, value in data_dict.items():
        setattr(unidad, key, value)
    uow.session.add(unidad)
    uow.session.flush()
    uow.session.refresh(unidad)
    return unidad


def delete(uow: UnidadMedidaUnitOfWork, unidad_id: int) -> bool:
    unidad = uow.session.get(UnidadMedida, unidad_id)
    if not unidad:
        return False
    uow.session.delete(unidad)
    uow.session.flush()
    return True
