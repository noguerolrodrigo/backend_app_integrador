from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

from alembic import context

# Importar todos los modelos para que SQLModel.metadata los registre
from app.modules.ingrediente.model import Ingrediente          # noqa: F401
from app.modules.producto.model import Producto                # noqa: F401
from app.modules.producto_ingrediente.model import ProductoIngrediente  # noqa: F401
from app.modules.producto_categoria.model import ProductoCategoria      # noqa: F401
from app.modules.categoria.model import Categoria              # noqa: F401
from app.modules.usuario.models import Usuario, Rol, UsuarioRol         # noqa: F401
from app.modules.pedido.models import Pedido, DetallePedido, HistorialEstadoPedido  # noqa: F401
from app.modules.direccion.models import DireccionEntrega      # noqa: F401
from app.modules.unidad_medida.model import UnidadMedida       # noqa: F401
from app.modules.pagos.model import Pago                       # noqa: F401
from app.modules.auth.model import RefreshToken                # noqa: F401
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", settings.database_url)

target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
