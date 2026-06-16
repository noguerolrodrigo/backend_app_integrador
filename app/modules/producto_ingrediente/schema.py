from decimal import Decimal

from sqlmodel import Field, SQLModel


class ProductoIngredienteCreate(SQLModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool = False
    cantidad: Decimal = Field(gt=0, decimal_places=3)
    unidad_medida_id: int


class ProductoIngredienteRead(SQLModel):
    producto_id: int
    ingrediente_id: int
    es_removible: bool
    cantidad: Decimal
    unidad_medida_id: int
