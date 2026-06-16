# Backend API - FastAPI & PostgreSQL

API REST desarrollada con **FastAPI** y **SQLModel**, implementando una arquitectura limpia con patrón **Unit of Work Modular**, repositorios genéricos y seguridad basada en **JWT** con control de roles (RBAC).

## Tecnologías Principales
* **Framework:** FastAPI
* **ORM:** SQLModel / SQLAlchemy
* **Base de Datos:** PostgreSQL
* **Seguridad:** OAuth2 con JWT, hashing con Bcrypt (12 rounds).
* **Patrones:** Repository Pattern, Unit of Work (Context Managers).

## Requisitos Previos
* Python 3.11 o superior.
* PostgreSQL instalado y corriendo.

## Configuración del Entorno (.env)
Crear un archivo `.env` en la raíz del proyecto con la siguiente estructura:

```env
POSTGRES_DB=parcial2
POSTGRES_USER=postgres
POSTGRES_PASSWORD=tu_contraseña
DATABASE_URL=postgresql+psycopg://postgres:tu_contraseña@localhost:5432/parcial2

# JWT Config (Reemplazar SECRET_KEY en producción)
SECRET_KEY=c13ffb41730cbf6c13e53e49cc20a3b20cd0440de0f00497e2cf5ead7144d430
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30