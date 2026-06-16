"""Configuración global de pytest para el backend.

Usa la base PostgreSQL real (parcial2) via TestClient.
Cada test limpia las tablas después de ejecutarse para asegurar aislamiento.
"""

from typing import Generator
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine, text
from app.main import app
from app.core.config import settings

# Credenciales admin del seed data
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"
LOGIN_URL = "/api/v1/auth/login"


@pytest.fixture(scope="session")
def db_engine():
    """Engine compartido para toda la sesión de tests"""
    engine = create_engine(settings.database_url, echo=False)
    SQLModel.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables(db_engine):
    """Limpia todas las tablas antes de cada test (en orden inverso por FK)"""
    yield  # corre el test
    with Session(db_engine) as session:
        for table in reversed(SQLModel.metadata.sorted_tables):
            session.execute(
                text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE")
            )
        session.commit()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Cliente HTTP de prueba — el lifespan crea tablas + seed data al iniciar"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def admin_token():
    """Obtiene token JWT de admin (session-scoped, se loguea una sola vez)"""
    with TestClient(app) as c:
        resp = c.post(LOGIN_URL, json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
        })
        if resp.status_code == 200:
            return resp.json()["access_token"]
        return None


@pytest.fixture
def auth_headers(admin_token):
    """Headers con token de admin para usar en tests que requieren auth"""
    if admin_token:
        return {"Authorization": f"Bearer {admin_token}"}
    return {}


@pytest.fixture(autouse=True)
def reset_rate_limits():
    """Limpia el estado de rate limiting entre tests para evitar interferencias."""
    yield
    from app.core.rate_limit import reset_for_ip
    reset_for_ip("testclient")
    reset_for_ip("127.0.0.1")
