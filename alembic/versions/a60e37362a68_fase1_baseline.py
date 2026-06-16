"""fase1_baseline

Revision ID: a60e37362a68
Revises:
Create Date: 2026-06-15 08:28:40.392742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'a60e37362a68'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. unidad_medida (sin FKs, referenciada por producto e ingrediente)
    op.create_table('unidad_medida',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('simbolo', sqlmodel.sql.sqltypes.AutoString(length=10), nullable=False),
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
        sa.UniqueConstraint('simbolo'),
    )

    # 2. usuario (sin FKs, referenciado por casi todo)
    op.create_table('usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('apellido', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('password_hash', sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_usuario_email'), 'usuario', ['email'], unique=True)

    # 3. rol (sin FKs)
    op.create_table('rol',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('codigo', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('descripcion', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_rol_nombre'), 'rol', ['nombre'], unique=True)
    op.create_index(op.f('ix_rol_codigo'), 'rol', ['codigo'], unique=True)

    # 4. categoria (self-FK nullable a parent_id)
    op.create_table('categoria',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('descripcion', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('imagen_url', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('parent_id', sa.Integer(), nullable=True),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['categoria.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # 5. ingrediente — SIN stock_cantidad ni deleted_at (los añade fase2)
    op.create_table('ingrediente',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('descripcion', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('es_alergeno', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )

    # 6. producto — SIN unidad_venta_id (lo añade fase2)
    op.create_table('producto',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column('descripcion', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('precio_base', sa.Float(), nullable=False),
        sa.Column('imagenes_url', sa.JSON(), nullable=True),
        sa.Column('stock_cantidad', sa.Integer(), nullable=False),
        sa.Column('disponible', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # 7. usuario_rol (tabla intermedia N:N)
    op.create_table('usuario_rol',
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('rol_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rol_id'], ['rol.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('usuario_id', 'rol_id'),
    )

    # 8. producto_categoria (tabla intermedia N:N con metadato)
    op.create_table('producto_categoria',
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=False),
        sa.Column('es_principal', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['categoria_id'], ['categoria.id'], ),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id'], ),
        sa.PrimaryKeyConstraint('producto_id', 'categoria_id'),
    )

    # 9. producto_ingrediente — SIN cantidad ni unidad_medida_id (los añade fase2)
    op.create_table('producto_ingrediente',
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('ingrediente_id', sa.Integer(), nullable=False),
        sa.Column('es_removible', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['ingrediente_id'], ['ingrediente.id'], ),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id'], ),
        sa.PrimaryKeyConstraint('producto_id', 'ingrediente_id'),
    )

    # 10. pedido (enums estado/forma_pago almacenados como VARCHAR)
    op.create_table('pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('numero_pedido', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('estado', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('forma_pago', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('monto_total', sa.Float(), nullable=False),
        sa.Column('direccion_entrega', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column('observaciones', sqlmodel.sql.sqltypes.AutoString(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pedido_numero_pedido'), 'pedido', ['numero_pedido'], unique=True)
    op.create_index(op.f('ix_pedido_estado'), 'pedido', ['estado'], unique=False)
    op.create_index(op.f('ix_pedido_usuario_id'), 'pedido', ['usuario_id'], unique=False)

    # 11. detalle_pedido (snapshot del producto en el momento de la compra)
    op.create_table('detalle_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('producto_id', sa.Integer(), nullable=False),
        sa.Column('nombre_producto', sqlmodel.sql.sqltypes.AutoString(length=150), nullable=False),
        sa.Column('precio_unitario', sa.Float(), nullable=False),
        sa.Column('cantidad', sa.Integer(), nullable=False),
        sa.Column('subtotal', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ),
        sa.ForeignKeyConstraint(['producto_id'], ['producto.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_detalle_pedido_pedido_id'), 'detalle_pedido', ['pedido_id'], unique=False)
    op.create_index(op.f('ix_detalle_pedido_producto_id'), 'detalle_pedido', ['producto_id'], unique=False)

    # 12. historial_estado_pedido (log append-only de transiciones de estado)
    op.create_table('historial_estado_pedido',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pedido_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('estado_anterior', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('estado_nuevo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('razon', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_historial_estado_pedido_pedido_id'), 'historial_estado_pedido', ['pedido_id'], unique=False)

    # 13. direccion_entrega
    op.create_table('direccion_entrega',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('alias', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=False),
        sa.Column('calle', sqlmodel.sql.sqltypes.AutoString(length=200), nullable=False),
        sa.Column('numero', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column('apartamento', sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column('localidad', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column('codigo_postal', sqlmodel.sql.sqltypes.AutoString(length=20), nullable=True),
        sa.Column('provincia', sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column('notas', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column('es_principal', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuario.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_direccion_entrega_usuario_id'), 'direccion_entrega', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_direccion_entrega_es_principal'), 'direccion_entrega', ['es_principal'], unique=False)


def downgrade() -> None:
    # Orden inverso al de creación (primero las tablas con FKs salientes)
    op.drop_index(op.f('ix_direccion_entrega_es_principal'), table_name='direccion_entrega')
    op.drop_index(op.f('ix_direccion_entrega_usuario_id'), table_name='direccion_entrega')
    op.drop_table('direccion_entrega')

    op.drop_index(op.f('ix_historial_estado_pedido_pedido_id'), table_name='historial_estado_pedido')
    op.drop_table('historial_estado_pedido')

    op.drop_index(op.f('ix_detalle_pedido_producto_id'), table_name='detalle_pedido')
    op.drop_index(op.f('ix_detalle_pedido_pedido_id'), table_name='detalle_pedido')
    op.drop_table('detalle_pedido')

    op.drop_index(op.f('ix_pedido_usuario_id'), table_name='pedido')
    op.drop_index(op.f('ix_pedido_estado'), table_name='pedido')
    op.drop_index(op.f('ix_pedido_numero_pedido'), table_name='pedido')
    op.drop_table('pedido')

    op.drop_table('producto_ingrediente')
    op.drop_table('producto_categoria')
    op.drop_table('usuario_rol')
    op.drop_table('producto')
    op.drop_table('ingrediente')
    op.drop_table('categoria')

    op.drop_index(op.f('ix_rol_codigo'), table_name='rol')
    op.drop_index(op.f('ix_rol_nombre'), table_name='rol')
    op.drop_table('rol')

    op.drop_index(op.f('ix_usuario_email'), table_name='usuario')
    op.drop_table('usuario')

    op.drop_table('unidad_medida')
