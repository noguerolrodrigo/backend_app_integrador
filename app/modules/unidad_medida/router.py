from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError

from app.core.deps import require_role
from app.modules.unidad_medida import service
from app.modules.unidad_medida.schema import (
    UnidadMedidaCreate,
    UnidadMedidaRead,
    UnidadMedidaUpdate,
)
from app.modules.unidad_medida.unidad_medida_uow import UnidadMedidaUnitOfWork

router = APIRouter(prefix="/api/v1/unidades-medida", tags=["Unidades de Medida"])


@router.get("/", response_model=list[UnidadMedidaRead], status_code=status.HTTP_200_OK)
def get_all(limit: int = Query(100, ge=1, le=500)):
    with UnidadMedidaUnitOfWork() as uow:
        return service.get_all(uow, limit)


@router.get("/{unidad_id}", response_model=UnidadMedidaRead, status_code=status.HTTP_200_OK)
def get_by_id(unidad_id: int = Path(..., gt=0)):
    with UnidadMedidaUnitOfWork() as uow:
        unidad = service.get_by_id(uow, unidad_id)
        if not unidad:
            raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
        return unidad


@router.post("/", response_model=UnidadMedidaRead, status_code=status.HTTP_201_CREATED)
def create(
    data: UnidadMedidaCreate,
    _=Depends(require_role(["ADMIN"])),
):
    try:
        with UnidadMedidaUnitOfWork() as uow:
            return service.create(uow, data)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe una unidad con ese nombre o símbolo")


@router.put("/{unidad_id}", response_model=UnidadMedidaRead, status_code=status.HTTP_200_OK)
def update(
    data: UnidadMedidaUpdate,
    unidad_id: int = Path(..., gt=0),
    _=Depends(require_role(["ADMIN"])),
):
    try:
        with UnidadMedidaUnitOfWork() as uow:
            resultado = service.update(uow, unidad_id, data.model_dump(exclude_unset=True))
            if not resultado:
                raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
            return resultado
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(status_code=409, detail="Ya existe una unidad con ese nombre o símbolo")


@router.delete("/{unidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    unidad_id: int = Path(..., gt=0),
    _=Depends(require_role(["ADMIN"])),
):
    try:
        with UnidadMedidaUnitOfWork() as uow:
            encontrado = service.delete(uow, unidad_id)
            if not encontrado:
                raise HTTPException(status_code=404, detail="Unidad de medida no encontrada")
    except HTTPException:
        raise
    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar: la unidad está en uso por algún producto o ingrediente",
        )
