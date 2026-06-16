"""Tests del módulo Categoría — soft delete, jerarquía, endpoint público"""

import hashlib
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.security import create_access_token
from app.modules.usuario.models import Usuario, Rol, UsuarioRol
from app.modules.categoria.model import Categoria
from app.modules.producto.model import Producto
from app.modules.producto_categoria.model import ProductoCategoria

BASE_URL = "/api/v1/categorias/"


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def admin_token(client: TestClient) -> str:
    """Crea un usuario ADMIN y devuelve su token JWT"""
    # Usar una sesión directa para crear el usuario ADMIN
    from app.core.database import engine

    with Session(engine) as session:
        # Crear rol ADMIN si no existe
        rol = session.exec(
            Rol.__table__.select().where(Rol.nombre == "ADMIN")
        ).first()
        if not rol:
            rol = Rol(nombre="ADMIN", codigo="ADMIN", descripcion="Test admin")
            session.add(rol)
            session.flush()

        # Crear usuario
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256", "admin123".encode("utf-8"), bytes.fromhex(salt), 100000
        )
        password_hash = f"{salt}${pwd_hash.hex()}"

        user = Usuario(
            nombre="Test",
            apellido="Admin",
            email="testadmin@test.com",
            password_hash=password_hash,
            activo=True,
        )
        session.add(user)
        session.flush()

        # Asignar rol ADMIN
        ur = UsuarioRol(usuario_id=user.id, rol_id=rol.id)
        session.add(ur)
        session.commit()

        # Generar token
        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "roles": ["ADMIN"],
        })

    return token


@pytest.fixture
def auth_headers(admin_token: str) -> dict:
    return {"Authorization": f"Bearer {admin_token}"}


# ── Helpers ───────────────────────────────────────────────────────────


def create_categoria(client, headers, **kwargs):
    data = {
        "nombre": kwargs.get("nombre", "Test"),
        "descripcion": kwargs.get("descripcion", None),
        "imagen_url": kwargs.get("imagen_url", None),
        "parent_id": kwargs.get("parent_id", None),
    }
    return client.post(BASE_URL, json=data, headers=headers)


def create_producto(session, nombre="Producto Test", precio=100.0, disponible=True):
    p = Producto(
        nombre=nombre,
        precio_base=precio,
        disponible=disponible,
        stock_cantidad=10,
    )
    session.add(p)
    session.flush()
    return p


def link_producto_categoria(session, producto_id, categoria_id):
    pc = ProductoCategoria(producto_id=producto_id, categoria_id=categoria_id)
    session.add(pc)
    session.commit()


# ── CRUD Tests (admin) ────────────────────────────────────────────────


def test_crear_categoria(client, auth_headers):
    """POST /api/v1/categorias/ debe crear una categoría"""
    response = create_categoria(client, auth_headers, nombre="Pizzas", descripcion="Todas las pizzas")
    assert response.status_code == 201
    data = response.json()
    assert data["nombre"] == "Pizzas"
    assert data["descripcion"] == "Todas las pizzas"
    assert "id" in data
    assert data["deleted_at"] is None


def test_crear_categoria_sin_auth(client):
    """POST sin token debe dar 401 o 422"""
    response = client.post(BASE_URL, json={"nombre": "NoAuth"})
    # Missing Authorization header triggers FastAPI validation error (422)
    # or can be 401 depending on version
    assert response.status_code in (401, 422)


def test_crear_categoria_con_token_invalido(client):
    """POST con token invalido debe dar 401"""
    response = client.post(
        BASE_URL,
        json={"nombre": "NoAuth"},
        headers={"Authorization": "Bearer token-invalido"},
    )
    assert response.status_code == 401


def test_listar_categorias(client, auth_headers):
    """GET /api/v1/categorias/ debe listar solo activas"""
    create_categoria(client, auth_headers, nombre="Bebidas")
    create_categoria(client, auth_headers, nombre="Pizzas")

    response = client.get(BASE_URL, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    nombres = [c["nombre"] for c in data]
    assert "Bebidas" in nombres
    assert "Pizzas" in nombres


def test_listar_categorias_sin_auth(client):
    """GET / sin auth debe dar 401 o 422"""
    response = client.get(BASE_URL)
    assert response.status_code in (401, 422)


def test_obtener_categoria_por_id(client, auth_headers):
    """GET /api/v1/categorias/{id} debe retornar una categoría"""
    created = create_categoria(client, auth_headers, nombre="Postres").json()
    response = client.get(f"{BASE_URL}{created['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["nombre"] == "Postres"


def test_obtener_categoria_inexistente(client, auth_headers):
    """GET /api/v1/categorias/{id} con id inexistente debe retornar 404"""
    response = client.get(f"{BASE_URL}99999", headers=auth_headers)
    assert response.status_code == 404


def test_actualizar_categoria(client, auth_headers):
    """PUT /api/v1/categorias/{id} debe actualizar la categoría"""
    created = create_categoria(client, auth_headers, nombre="Temporal").json()
    response = client.put(
        f"{BASE_URL}{created['id']}",
        json={"nombre": "Actualizada", "descripcion": "Nueva desc", "parent_id": None},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["nombre"] == "Actualizada"


# ── Soft delete tests ─────────────────────────────────────────────────


def test_soft_delete_categoria(client, auth_headers):
    """DELETE debe hacer soft delete (204), luego GET da 404"""
    created = create_categoria(client, auth_headers, nombre="Eliminar").json()
    cat_id = created["id"]

    delete_resp = client.delete(f"{BASE_URL}{cat_id}", headers=auth_headers)
    assert delete_resp.status_code == 204

    # Verificar que ya no aparece (404 para admin)
    get_resp = client.get(f"{BASE_URL}{cat_id}", headers=auth_headers)
    assert get_resp.status_code == 404


def test_delete_categoria_con_productos_activos_409(client, auth_headers):
    """DELETE de categoría con productos activos debe dar 409"""
    from app.core.database import engine

    # Crear categoría
    created = create_categoria(client, auth_headers, nombre="ConProductos").json()
    cat_id = created["id"]

    # Crear producto activo y vincularlo
    with Session(engine) as session:
        prod = create_producto(session, nombre="Producto Activo")
        link_producto_categoria(session, prod.id, cat_id)

    # Intentar eliminar → 409
    response = client.delete(f"{BASE_URL}{cat_id}", headers=auth_headers)
    assert response.status_code == 409
    assert "producto" in response.json()["detail"].lower()


def test_delete_categoria_con_productos_inactivos_204(client, auth_headers):
    """DELETE de categoría con solo productos inactivos debe funcionar"""
    from app.core.database import engine

    created = create_categoria(client, auth_headers, nombre="ConInactivos").json()
    cat_id = created["id"]

    with Session(engine) as session:
        # Producto no disponible
        prod = create_producto(session, nombre="Inactivo", disponible=False)
        link_producto_categoria(session, prod.id, cat_id)

    # Eliminar → 204 (producto inactivo no bloquea)
    response = client.delete(f"{BASE_URL}{cat_id}", headers=auth_headers)
    assert response.status_code == 204


# ── Hierarchy tests ───────────────────────────────────────────────────


def test_crear_categoria_con_parent(client, auth_headers):
    """Crear categoría hija debe funcionar con parent_id válido"""
    parent = create_categoria(client, auth_headers, nombre="Padre").json()
    child = create_categoria(client, auth_headers, nombre="Hija", parent_id=parent["id"])
    assert child.status_code == 201
    assert child.json()["parent_id"] == parent["id"]


def test_crear_categoria_con_parent_inexistente_404(client, auth_headers):
    """Crear categoría con parent_id inexistente debe dar 404"""
    response = create_categoria(client, auth_headers, nombre="Hija", parent_id=99999)
    assert response.status_code == 404


def test_actualizar_categoria_parent_self_reference_422(client, auth_headers):
    """Actualizar parent_id al mismo id debe dar 422"""
    created = create_categoria(client, auth_headers, nombre="SelfRef").json()
    response = client.put(
        f"{BASE_URL}{created['id']}",
        json={"parent_id": created["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ── Public endpoint tests ─────────────────────────────────────────────


def test_public_endpoint_sin_auth(client, auth_headers):
    """GET /public debe funcionar sin autenticación"""
    create_categoria(client, auth_headers, nombre="Visible")

    response = client.get(f"{BASE_URL}public")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_public_endpoint_excluye_soft_deleted(client, auth_headers):
    """GET /public no debe mostrar categorías soft-deleteadas"""
    created = create_categoria(client, auth_headers, nombre="ProntoEliminada").json()
    cat_id = created["id"]

    # Soft delete
    client.delete(f"{BASE_URL}{cat_id}", headers=auth_headers)

    # No debe aparecer en público
    response = client.get(f"{BASE_URL}public")
    assert response.status_code == 200
    nombres = [i["nombre"] for i in response.json()["items"]]
    assert "ProntoEliminada" not in nombres


def test_public_endpoint_filtro_parent_id(client, auth_headers):
    """GET /public con parent_id debe filtrar"""
    parent = create_categoria(client, auth_headers, nombre="PadrePublic").json()
    create_categoria(client, auth_headers, nombre="HijaPublic", parent_id=parent["id"])

    # Filtrar por parent_id
    response = client.get(f"{BASE_URL}public?parent_id={parent['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert all(i["parent_id"] == parent["id"] for i in data["items"])


def test_public_endpoint_paginacion(client, auth_headers):
    """GET /public debe respetar limit y offset"""
    for i in range(5):
        create_categoria(client, auth_headers, nombre=f"Pagina{i}")

    # Primera página: limit=2
    page1 = client.get(f"{BASE_URL}public?limit=2&offset=0")
    assert page1.status_code == 200
    assert len(page1.json()["items"]) == 2

    # Segunda página
    page2 = client.get(f"{BASE_URL}public?limit=2&offset=2")
    assert page2.status_code == 200
    assert len(page2.json()["items"]) == 2

    # Los nombres deben ser diferentes entre páginas
    names1 = [i["nombre"] for i in page1.json()["items"]]
    names2 = [i["nombre"] for i in page2.json()["items"]]
    assert set(names1).isdisjoint(set(names2))


def test_public_endpoint_sin_categorias(client):
    """GET /public sin categorías debe devolver lista vacía"""
    response = client.get(f"{BASE_URL}public")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
