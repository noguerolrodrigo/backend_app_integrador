from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Session
from app.core.database import engine
from app.db.seed import seed_database

from app.modules.categoria.router import router as categoria_router
from app.modules.ingrediente.router import router as ingrediente_router
from app.modules.producto.router import router as producto_router
from app.modules.producto_categoria.router import router as producto_categoria_router
from app.modules.producto_ingrediente.router import router as producto_ingrediente_router
from app.modules.usuario.router import router as usuario_router
from app.modules.pedido.router import router as pedido_router
from app.modules.pedido.ws_router import ws_router
from app.modules.pagos.router import router as pagos_router
from app.modules.direccion.router import router as direccion_router
from app.modules.auth.router import router as auth_router
from app.modules.unidad_medida.router import router as unidad_medida_router
from app.modules.estadisticas.router import router as estadisticas_router
from app.modules.uploads.router import router as uploads_router

from app.modules.categoria.model import Categoria
from app.modules.ingrediente.model import Ingrediente  
from app.modules.producto.model import Producto 
from app.modules.producto_categoria.model import ProductoCategoria  
from app.modules.producto_ingrediente.model import ProductoIngrediente
from app.modules.usuario.models import Usuario, Rol, UsuarioRol  
from app.modules.pedido.models import Pedido, DetallePedido, HistorialEstadoPedido
from app.modules.pagos.model import Pago  # noqa: F401 — registra tabla en metadata
from app.modules.direccion.models import DireccionEntrega
from app.modules.unidad_medida.model import UnidadMedida
from app.modules.auth.model import RefreshToken  # noqa: F401 — registra tabla en metadata

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear todas las tablas
    SQLModel.metadata.create_all(engine)
    
    # Poblar seed data y COMMITEAR — sin commit los datos se pierden al cerrar sesión
    with Session(engine) as session:
        seed_database(session)
        session.commit()
    
    yield


app = FastAPI(
    title="API Parcial FastAPI + SQLModel",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5175",
        "http://127.0.0.1:5175",
        "http://localhost:5176",
        "http://127.0.0.1:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos para imágenes subidas
media_dir = Path(__file__).resolve().parent.parent / "media"
media_dir.mkdir(exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

app.include_router(auth_router)
app.include_router(categoria_router)
app.include_router(ingrediente_router)
app.include_router(producto_router)
app.include_router(producto_categoria_router)
app.include_router(producto_ingrediente_router)
app.include_router(usuario_router)
app.include_router(pedido_router)
app.include_router(ws_router)
app.include_router(pagos_router)
app.include_router(direccion_router)
app.include_router(unidad_medida_router)
app.include_router(estadisticas_router)
app.include_router(uploads_router)


@app.get("/")
def healthcheck():
    return {"message": "Backend activo"}
