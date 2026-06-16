"""
Utilidades de seguridad centralizadas.

Responsabilidades:
- Hashing de contraseñas (bcrypt vía passlib)
- Generación y validación de JWT (HS256 con python-jose)

Motivación:
- Evitar duplicación de lógica de seguridad
- Permitir reutilización (routers, seeds, tests, etc.)
- Mantener separación de capas (no mezclar con endpoints)
"""

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings


# ─────────────────────────────────────────────────────────────────────────────
# HASHING DE CONTRASEÑAS (bcrypt vía passlib)
# ─────────────────────────────────────────────────────────────────────────────

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """
    Genera hash bcrypt de una contraseña en texto plano.

    bcrypt incluye salt automáticamente, cada hash es distinto.
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verifica una contraseña en texto plano contra su hash.

    Internamente passlib extrae el salt, recalcula y compara
    de forma segura contra timing attacks.
    """
    return pwd_context.verify(plain, hashed)


# ─────────────────────────────────────────────────────────────────────────────
# JWT — GENERACIÓN Y VALIDACIÓN
# ─────────────────────────────────────────────────────────────────────────────


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Genera un JWT firmado (HS256).

    Parámetros:
        data: payload base (ej: {"sub": email, "user_id": id, "roles": [...]})
        expires_delta: override opcional del tiempo de expiración

    Retorna:
        Token JWT firmado como string
    """
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )

    to_encode.update({
        "type": "access",
        "exp": expire,
    })

    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict | None:
    """
    Decodifica y valida un JWT.

    Validaciones:
    - Firma válida
    - No expirado
    - Tipo "access"

    Retorna:
        dict → payload válido
        None → token inválido
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

        if payload.get("type") != "access":
            return None

        return payload

    except JWTError:
        return None


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(days=settings.refresh_token_expire_days)
    )
    to_encode.update({"type": "refresh", "exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


def decode_refresh_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            return None
        return payload
    except JWTError:
        return None
