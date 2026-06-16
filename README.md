# 🍔 Food Store — Backend API

Backend del Trabajo Práctico Integrador de **Programación 4 (TUP)**. API REST construida con **FastAPI** y **SQLModel**, con arquitectura en capas (Router → Service → Unit of Work → Repository → Model), seguridad **JWT + RBAC**, notificaciones en tiempo real por **WebSocket**, pasarela de pagos **MercadoPago** y gestión de imágenes con **Cloudinary**.

## Tecnologías

- **Framework:** FastAPI (REST + WebSocket)
- **ORM:** SQLModel / SQLAlchemy
- **Base de datos:** PostgreSQL 15+
- **Migraciones:** Alembic
- **Seguridad:** JWT (access + refresh), hashing bcrypt (cost ≥ 12), RBAC con 4 roles
- **Integraciones:** MercadoPago (Checkout PRO + webhook IPN), Cloudinary
- **Tests:** pytest + TestClient

## Requisitos previos

- Python 3.11 o superior
- PostgreSQL 15+ instalado y corriendo
- Una base de datos creada (por defecto el proyecto usa `parcial2`)

## Instalación y puesta en marcha

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPO>
cd backend_app_integrador
```

### 2. Crear y activar un entorno virtual

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar las variables de entorno

Copiá el archivo de ejemplo y completá tus datos:

```bash
cp .env.example .env
```

Luego editá `.env` con tus credenciales reales. La estructura es:

```env
# Base de datos (PostgreSQL)
DATABASE_URL=postgresql+psycopg://postgres:TU_PASSWORD@localhost:5432/parcial2

# JWT — generar la clave con: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=tu-clave-secreta-de-32-bytes
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# MercadoPago (credenciales de prueba)
MP_ACCESS_TOKEN=TEST-xxxx
MP_PUBLIC_KEY=TEST-xxxx
MP_NOTIFICATION_URL=https://tu-dominio.ngrok.io/api/v1/pagos/webhook

# Cloudinary
CLOUDINARY_CLOUD_NAME=tu-cloud-name
CLOUDINARY_API_KEY=tu-api-key
CLOUDINARY_API_SECRET=tu-api-secret
```

> ⚠️ El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio.
>
> Las credenciales de **MercadoPago** y **Cloudinary** que figuran arriba son de ejemplo. Para que esas funcionalidades operen de verdad hay que reemplazarlas por credenciales reales (ambos servicios tienen cuenta gratuita). Los tests funcionan sin credenciales reales porque mockean esos servicios.

### 5. Aplicar las migraciones de la base de datos

```bash
alembic upgrade head
```

Esto crea todas las tablas en tu base de datos según el estado más reciente del modelo.

### 6. Levantar el servidor

```bash
uvicorn app.main:app --reload
```

El servidor arranca en `http://localhost:8000`. **El seed de datos iniciales se ejecuta automáticamente** al iniciar la aplicación: crea los roles (ADMIN, STOCK, PEDIDOS, CLIENT), los estados de pedido, las formas de pago, las unidades de medida y un usuario administrador.

**Usuario administrador por defecto:**
- Email: `admin@example.com`
- Contraseña: `admin123`

## Documentación de la API

Con el servidor corriendo:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Contrato OpenAPI (JSON):** http://localhost:8000/openapi.json

## Ejecutar los tests

```bash
python -m pytest
```

Para ver el detalle de cada test:

```bash
python -m pytest -v
```

Los tests usan SQLite en memoria, por lo que no afectan tu base de datos de PostgreSQL.

## Estructura del proyecto

```
backend_app_integrador/
├── alembic/              # Migraciones de base de datos
├── app/
│   ├── core/             # Configuración, seguridad, UoW base, WebSocket manager, rate limiting
│   ├── db/               # Seed de datos iniciales
│   └── modules/          # Módulos por feature (auth, usuarios, productos, pedidos, pagos, etc.)
├── test/                 # Tests de integración
├── .env.example          # Plantilla de variables de entorno
├── alembic.ini
├── requirements.txt
└── README.md
```

## Arquitectura

El backend aplica una arquitectura en capas con flujo de dependencias unidireccional:

```
Router → Service → Unit of Work → Repository → Model
```

- **Unit of Work:** gestiona la transacción (commit/rollback automático). Ningún service hace `commit` directo.
- **WebSocket:** el `WSManager` emite notificaciones de cambios de estado de pedidos **después del commit**, fuera del bloque transaccional.
- **Patrones aplicados:** Repository, Unit of Work, Snapshot (precios inmutables en pedidos), Soft Delete, Audit Trail append-only, State Machine (FSM de pedidos), pagos idempotentes.

## Funcionalidades principales

- Autenticación JWT con access + refresh tokens, logout con revocación y rate limiting
- Catálogo de productos con categorías jerárquicas, ingredientes y unidades de medida
- Carrito y gestión de pedidos con máquina de estados y trazabilidad completa
- Pagos con MercadoPago (Checkout PRO) y webhook de confirmación
- Notificaciones en tiempo real vía WebSocket
- Gestión de imágenes con Cloudinary
- Panel de estadísticas (KPIs) para administradores
