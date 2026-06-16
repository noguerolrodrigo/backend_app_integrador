from fastapi import APIRouter, Depends, HTTPException, Query, Path, status

from app.modules.producto_categoria import service
from app.modules.producto_categoria.producto_categoria_uow import (
    ProductoCategoriaUnitOfWork,
)
from app.modules.producto_categoria.schema import ProductoCategoriaCreate

router = APIRouter(prefix="/producto-categoria", tags=["ProductoCategoria"])


@router.post("/", status_code=status.HTTP_201_CREATED)
def create(data: ProductoCategoriaCreate):
    with ProductoCategoriaUnitOfWork() as uow:
        resultado = service.create_relation(
            uow,
            data.producto_id,
            data.categoria_id,
            data.es_principal,
        )
        return resultado


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    producto_id: int = Query(..., gt=0),
    categoria_id: int = Query(..., gt=0),
):
    with ProductoCategoriaUnitOfWork() as uow:
        deleted = service.delete_relation(uow, producto_id, categoria_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Relación no encontrada")

        return


@router.get("/producto/{producto_id}", status_code=status.HTTP_200_OK)
def by_producto(producto_id: int = Path(..., gt=0)):
    with ProductoCategoriaUnitOfWork() as uow:
        return service.get_by_producto(uow, producto_id)


@router.get("/categoria/{categoria_id}", status_code=status.HTTP_200_OK)
def by_categoria(categoria_id: int = Path(..., gt=0)):
    with ProductoCategoriaUnitOfWork() as uow:
        return service.get_by_categoria(uow, categoria_id)
