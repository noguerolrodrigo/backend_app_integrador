from datetime import datetime

from sqlmodel import select

from app.modules.ingrediente.model import Ingrediente
from app.modules.ingrediente.ingrediente_uow import IngredienteUnitOfWork


def create(uow: IngredienteUnitOfWork, data) -> Ingrediente:
    ingrediente = Ingrediente(**data.model_dump())
    uow.session.add(ingrediente)
    uow.session.flush()
    uow.session.refresh(ingrediente)
    return ingrediente


def get_all(uow: IngredienteUnitOfWork, limit: int) -> list[Ingrediente]:
    return list(
        uow.session.exec(
            select(Ingrediente).where(Ingrediente.deleted_at.is_(None)).limit(limit)
        ).all()
    )


def get_by_id(uow: IngredienteUnitOfWork, ingrediente_id: int) -> Ingrediente | None:
    ingrediente = uow.session.get(Ingrediente, ingrediente_id)
    if ingrediente and ingrediente.is_deleted():
        return None
    return ingrediente


def update(uow: IngredienteUnitOfWork, ingrediente_id: int, data_dict: dict) -> Ingrediente | None:
    ingrediente = get_by_id(uow, ingrediente_id)
    if not ingrediente:
        return None
    for key, value in data_dict.items():
        setattr(ingrediente, key, value)
    ingrediente.updated_at = datetime.utcnow()
    uow.session.add(ingrediente)
    uow.session.flush()
    uow.session.refresh(ingrediente)
    return ingrediente


def delete(uow: IngredienteUnitOfWork, ingrediente_id: int) -> bool:
    ingrediente = get_by_id(uow, ingrediente_id)
    if not ingrediente:
        return False
    ingrediente.deleted_at = datetime.utcnow()
    ingrediente.updated_at = datetime.utcnow()
    uow.session.add(ingrediente)
    uow.session.flush()
    return True


def restore(uow: IngredienteUnitOfWork, ingrediente_id: int) -> Ingrediente | None:
    ingrediente = uow.session.get(Ingrediente, ingrediente_id)
    if not ingrediente or not ingrediente.is_deleted():
        return None
    ingrediente.deleted_at = None
    ingrediente.updated_at = datetime.utcnow()
    uow.session.add(ingrediente)
    uow.session.flush()
    uow.session.refresh(ingrediente)
    return ingrediente
