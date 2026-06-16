from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status

from app.core.deps import get_current_user, require_role
from app.modules.producto.service import ProductoService
from app.modules.producto.producto_uow import ProductoUnitOfWork
from app.modules.producto.model import Producto
from app.modules.usuario.models import Usuario
from app.modules.ingrediente.schema import IngredienteRead
from app.modules.producto.schema import (
    ImagenProductoUpdate,
    ProductoCreate,
    ProductoRead,
    ProductoUpdate,
    ProductoUpdateDisponibilidad,
)

router = APIRouter(prefix="/api/v1/productos", tags=["Productos"])


@router.get("/", response_model=list[ProductoRead])
def get_all(
    min_precio: Annotated[float, Query(ge=0, description="Precio mínimo")] = 0,
    max_precio: Annotated[float, Query(ge=0, description="Precio máximo")] = 100000,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    offset: Annotated[int, Query(ge=0)] = 0,
    categoria_id: Annotated[Optional[int], Query(description="Filtrar por ID de categoría")] = None,
    disponible: Annotated[Optional[bool], Query(description="Filtrar por disponibilidad")] = None,
    search: Annotated[Optional[str], Query(min_length=1, description="Búsqueda textual por nombre o descripción")] = None,
):
    """Lista productos del catálogo con filtros combinados (público)"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        return service.get_filtered(
            min_precio=min_precio,
            max_precio=max_precio,
            limit=limit,
            offset=offset,
            categoria_id=categoria_id,
            disponible=disponible,
            search=search,
            include_deleted=False,
        )


@router.get("/{producto_id}", response_model=ProductoRead)
def get_by_id(
    producto_id: Annotated[int, Path(gt=0)],
):
    """Obtiene un producto por ID"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id)

        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        return producto


@router.post("/", response_model=ProductoRead, status_code=status.HTTP_201_CREATED)
def create(
    data: ProductoCreate,
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """Crea un nuevo producto"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = Producto(**data.model_dump())
        resultado = service.create(producto)
        return resultado


@router.put("/{producto_id}", response_model=ProductoRead)
def update(
    data: ProductoUpdate,
    producto_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """Actualiza un producto"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id)

        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")

        resultado = service.update(producto, data.model_dump(exclude_unset=True))
        return resultado


@router.patch("/{producto_id}/disponibilidad", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def update_disponibilidad(
    data: ProductoUpdateDisponibilidad,
    producto_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN", "STOCK"])),
):
    """Actualiza la disponibilidad de un producto"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        resultado = service.update_disponibilidad(producto, data.disponible)
        return resultado


@router.delete("/{producto_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    producto_id: Annotated[int, Path(gt=0)],
    hard_delete: Annotated[bool, Query(description="Si es True, elimina permanentemente")] = False,
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """Elimina un producto (soft delete por defecto)"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id, include_deleted=True)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        if hard_delete:
            service.hard_delete(producto)
        else:
            service.soft_delete(producto)
        return


@router.post("/{producto_id}/restaurar", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def restore(
    producto_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    """Restaura un producto que fue eliminado (soft delete)"""
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id, include_deleted=True)

        if not producto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado",
            )

        if not producto.is_deleted():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto no está eliminado",
            )

        resultado = service.restore(producto)
        return resultado


@router.patch("/{producto_id}/imagenes", response_model=ProductoRead, status_code=status.HTTP_200_OK)
def update_imagenes(
    data: ImagenProductoUpdate,
    producto_id: Annotated[int, Path(gt=0)],
    _: Usuario = Depends(require_role(["ADMIN"])),
):
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return service.update(producto, {"imagenes_url": data.imagenes_url})


@router.get("/{producto_id}/ingredientes", response_model=list[IngredienteRead])
def get_ingredientes(producto_id: Annotated[int, Path(gt=0)]):
    with ProductoUnitOfWork() as uow:
        service = ProductoService(uow)
        producto = service.get_by_id(producto_id)
        if not producto:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return producto.ingredientes
