from sqlmodel import select

from app.modules.producto_categoria.model import ProductoCategoria
from app.modules.producto_categoria.producto_categoria_uow import (
    ProductoCategoriaUnitOfWork,
)


def create_relation(
    uow: ProductoCategoriaUnitOfWork,
    producto_id: int,
    categoria_id: int,
    es_principal: bool = False,
):
    relation = ProductoCategoria(
        producto_id=producto_id,
        categoria_id=categoria_id,
        es_principal=es_principal,
    )

    uow.session.add(relation)
    uow.session.flush()
    uow.session.refresh(relation)
    return relation


def delete_relation(
    uow: ProductoCategoriaUnitOfWork,
    producto_id: int,
    categoria_id: int,
):
    statement = select(ProductoCategoria).where(
        ProductoCategoria.producto_id == producto_id,
        ProductoCategoria.categoria_id == categoria_id,
    )

    relation = uow.session.exec(statement).first()

    if not relation:
        return None

    uow.session.delete(relation)
    uow.session.flush()
    return relation


def get_by_producto(
    uow: ProductoCategoriaUnitOfWork,
    producto_id: int,
):
    statement = select(ProductoCategoria).where(
        ProductoCategoria.producto_id == producto_id
    )
    return uow.session.exec(statement).all()


def get_by_categoria(
    uow: ProductoCategoriaUnitOfWork,
    categoria_id: int,
):
    statement = select(ProductoCategoria).where(
        ProductoCategoria.categoria_id == categoria_id
    )
    return uow.session.exec(statement).all()
