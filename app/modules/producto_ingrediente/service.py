from sqlmodel import select

from app.modules.producto_ingrediente.model import ProductoIngrediente
from app.modules.producto_ingrediente.producto_ingrediente_uow import (
    ProductoIngredienteUnitOfWork,
)


def create_relation(
    uow: ProductoIngredienteUnitOfWork,
    producto_id: int,
    ingrediente_id: int,
    es_removible: bool,
    cantidad,
    unidad_medida_id: int,
):
    if cantidad <= 0:
        raise ValueError("cantidad debe ser mayor a 0")
    relation = ProductoIngrediente(
        producto_id=producto_id,
        ingrediente_id=ingrediente_id,
        es_removible=es_removible,
        cantidad=cantidad,
        unidad_medida_id=unidad_medida_id,
    )
    uow.session.add(relation)
    uow.session.flush()
    uow.session.refresh(relation)
    return relation


def delete_relation(
    uow: ProductoIngredienteUnitOfWork,
    producto_id: int,
    ingrediente_id: int,
):
    statement = select(ProductoIngrediente).where(
        ProductoIngrediente.producto_id == producto_id,
        ProductoIngrediente.ingrediente_id == ingrediente_id,
    )
    relation = uow.session.exec(statement).first()

    if not relation:
        return False

    uow.session.delete(relation)
    uow.session.flush()
    return True


def get_by_producto(
    uow: ProductoIngredienteUnitOfWork,
    producto_id: int,
):
    return uow.session.exec(
        select(ProductoIngrediente).where(
            ProductoIngrediente.producto_id == producto_id
        )
    ).all()


def get_by_ingrediente(
    uow: ProductoIngredienteUnitOfWork,
    ingrediente_id: int,
):
    return uow.session.exec(
        select(ProductoIngrediente).where(
            ProductoIngrediente.ingrediente_id == ingrediente_id
        )
    ).all()
