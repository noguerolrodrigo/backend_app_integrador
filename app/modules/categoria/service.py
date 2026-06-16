from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import select, func

from app.modules.categoria.model import Categoria
from app.modules.categoria.categoria_uow import CategoriaUnitOfWork
from app.modules.producto.model import Producto
from app.modules.producto_categoria.model import ProductoCategoria


class CategoriaService:

    def __init__(self, uow: CategoriaUnitOfWork):
        self.uow = uow

    # ── Admin: list (excludes soft-deleted) ──────────────────────────

    def get_all(self):
        stmt = (
            select(Categoria)
            .where(Categoria.deleted_at == None)
            .order_by(Categoria.nombre)
        )
        return self.uow.session.exec(stmt).all()

    # ── Admin: get by id (excludes soft-deleted) ─────────────────────

    def get_by_id(self, categoria_id: int):
        categoria = self.uow.session.get(Categoria, categoria_id)
        if categoria and categoria.is_deleted():
            return None
        return categoria

    # ── Admin: create ────────────────────────────────────────────────

    def create(self, categoria: Categoria):
        if categoria.parent_id is not None:
            self._validate_parent(categoria.parent_id)
        self.uow.session.add(categoria)
        self.uow.session.flush()
        return categoria

    # ── Admin: update ────────────────────────────────────────────────

    def update(self, db_categoria: Categoria, data: dict):
        parent_changed = "parent_id" in data

        if parent_changed and data["parent_id"] is not None:
            new_parent_id = data["parent_id"]

            # Self-reference check
            if new_parent_id == db_categoria.id:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Una categoría no puede ser padre de sí misma",
                )

            # Parent exists and is not deleted
            self._validate_parent(new_parent_id)

        for key, value in data.items():
            setattr(db_categoria, key, value)

        db_categoria.updated_at = datetime.utcnow()
        self.uow.session.add(db_categoria)
        self.uow.session.flush()
        return db_categoria

    # ── Admin: soft delete ───────────────────────────────────────────

    def delete(self, db_categoria: Categoria):
        # Check for active products linked to this category
        active_count = self._count_active_products(db_categoria.id)
        if active_count > 0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"No se puede eliminar la categoría porque tiene "
                    f"{active_count} producto(s) activo(s) asociado(s). "
                    f"Desvincule o desactive los productos primero."
                ),
            )

        # Soft delete
        db_categoria.deleted_at = datetime.utcnow()
        db_categoria.updated_at = datetime.utcnow()
        self.uow.session.add(db_categoria)
        self.uow.session.flush()

    # ── Public: paginated listing ────────────────────────────────────

    def get_public(
        self,
        parent_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
        search: Optional[str] = None,
    ):
        # Base query: only non-deleted
        stmt = (
            select(Categoria)
            .where(Categoria.deleted_at == None)
            .order_by(Categoria.nombre)
        )

        # Count query (same filters)
        count_stmt = (
            select(func.count())
            .select_from(Categoria)
            .where(Categoria.deleted_at == None)
        )

        # Search filter: ILIKE on nombre
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(Categoria.nombre.ilike(pattern))
            count_stmt = count_stmt.where(Categoria.nombre.ilike(pattern))

        if parent_id is not None:
            stmt = stmt.where(Categoria.parent_id == parent_id)
            count_stmt = count_stmt.where(Categoria.parent_id == parent_id)
        else:
            # If no parent_id filter, show root categories only
            stmt = stmt.where(Categoria.parent_id == None)
            count_stmt = count_stmt.where(Categoria.parent_id == None)

        total = self.uow.session.exec(count_stmt).one()
        items = self.uow.session.exec(stmt.offset(offset).limit(limit)).all()

        return items, total

    # ── Private helpers ──────────────────────────────────────────────

    def _validate_parent(self, parent_id: int):
        parent = self.uow.session.get(Categoria, parent_id)
        if not parent or parent.is_deleted():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="La categoría padre no existe o fue eliminada",
            )

    def _count_active_products(self, categoria_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(ProductoCategoria)
            .join(Producto, ProductoCategoria.producto_id == Producto.id)
            .where(
                ProductoCategoria.categoria_id == categoria_id,
                Producto.deleted_at == None,
                Producto.disponible == True,
            )
        )
        result = self.uow.session.exec(stmt).one()
        return result
