from fastapi import APIRouter, Depends, HTTPException, Path, status, Query

from app.core.deps import get_current_user, require_role
from app.modules.ingrediente import service
from app.modules.ingrediente.ingrediente_uow import IngredienteUnitOfWork
from app.modules.usuario.models import Usuario
from app.modules.ingrediente.schema import (
    IngredienteCreate,
    IngredienteUpdate,
    IngredienteRead,
)

router = APIRouter(prefix="/ingredientes", tags=["Ingredientes"])


@router.post("/", response_model=IngredienteRead, status_code=status.HTTP_201_CREATED)
def create(
    data: IngredienteCreate,
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    with IngredienteUnitOfWork() as uow:
        resultado = service.create(uow, data)
        return resultado


@router.get("/", response_model=list[IngredienteRead], status_code=status.HTTP_200_OK)
def get_all(
    limit: int = Query(10, ge=1, le=100),
):
    with IngredienteUnitOfWork() as uow:
        return service.get_all(uow, limit)


@router.get("/{ingrediente_id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def get_by_id(
    ingrediente_id: int = Path(..., gt=0),
):
    with IngredienteUnitOfWork() as uow:
        ingrediente = service.get_by_id(uow, ingrediente_id)

        if not ingrediente:
            raise HTTPException(status_code=404, detail="Ingrediente no encontrado")

        return ingrediente


@router.put("/{ingrediente_id}", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def update(
    data: IngredienteUpdate,
    ingrediente_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    with IngredienteUnitOfWork() as uow:
        resultado = service.update(uow, ingrediente_id, data.model_dump(exclude_unset=True))

        if not resultado:
            raise HTTPException(status_code=404, detail="Ingrediente no encontrado")

        return resultado


@router.delete("/{ingrediente_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    ingrediente_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    with IngredienteUnitOfWork() as uow:
        encontrado = service.delete(uow, ingrediente_id)
        if not encontrado:
            raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
        return None


@router.post("/{ingrediente_id}/restaurar", response_model=IngredienteRead, status_code=status.HTTP_200_OK)
def restaurar(
    ingrediente_id: int = Path(..., gt=0),
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    with IngredienteUnitOfWork() as uow:
        resultado = service.restore(uow, ingrediente_id)
        if not resultado:
            raise HTTPException(status_code=404, detail="Ingrediente no encontrado o no está eliminado")
        return resultado
