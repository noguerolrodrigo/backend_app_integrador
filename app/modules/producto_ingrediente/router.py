from fastapi import APIRouter, HTTPException, status

from app.modules.producto_ingrediente import service
from app.modules.producto_ingrediente.producto_ingrediente_uow import (
    ProductoIngredienteUnitOfWork,
)
from app.modules.producto_ingrediente.schema import (
    ProductoIngredienteCreate,
    ProductoIngredienteRead,
)

router = APIRouter(prefix="/producto-ingrediente", tags=["ProductoIngrediente"])


@router.post("/", response_model=ProductoIngredienteRead, status_code=status.HTTP_201_CREATED)
def create(data: ProductoIngredienteCreate):
    try:
        with ProductoIngredienteUnitOfWork() as uow:
            return service.create_relation(uow, **data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete(producto_id: int, ingrediente_id: int):
    with ProductoIngredienteUnitOfWork() as uow:
        deleted = service.delete_relation(uow, producto_id, ingrediente_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Relación no encontrada")


@router.get("/producto/{producto_id}", response_model=list[ProductoIngredienteRead])
def by_producto(producto_id: int):
    with ProductoIngredienteUnitOfWork() as uow:
        return service.get_by_producto(uow, producto_id)


@router.get("/ingrediente/{ingrediente_id}", response_model=list[ProductoIngredienteRead])
def by_ingrediente(ingrediente_id: int):
    with ProductoIngredienteUnitOfWork() as uow:
        return service.get_by_ingrediente(uow, ingrediente_id)
