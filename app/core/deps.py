"""
Dependencias de autenticación y autorización para FastAPI.

Este módulo define funciones que se inyectan con Depends() para:
- Extraer el token JWT del request (cookie HttpOnly o header Authorization)
- Validar autenticación (get_current_user)
- Validar permisos por roles (require_role)

Flujo típico:
    Request HTTP
        ↓
    oauth2_scheme → extrae el token Bearer (cookie o header)
        ↓
    get_current_user → decodifica JWT, busca el usuario en DB
        ↓
    require_role([...]) → valida permisos (RBAC)

Convenciones HTTP:
    401 → No autenticado (token inválido, ausente o expirado)
    403 → Autenticado pero sin permisos suficientes
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.security import decode_access_token
from app.modules.usuario.models import Usuario
from app.modules.usuario.usuario_uow import UsuarioUnitOfWork


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    """
    Extrae el token JWT primero de la cookie HttpOnly 'access_token'.
    Si no está en cookie, fallback al header Authorization (Bearer).

    Prioridad: cookie > header.
    """

    async def __call__(self, request: Request) -> str | None:
        # 1. Intentar desde cookie HttpOnly
        token = request.cookies.get("access_token")

        # 2. Fallback al header Authorization
        if not token:
            authorization = request.headers.get("Authorization")
            if authorization and authorization.startswith("Bearer "):
                token = authorization.split(" ")[1]

        if not token:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="No autenticado",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        return token


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Usuario:
    """
    Decodifica el JWT y retorna el Usuario correspondiente.

    Responsabilidades:
    - Validar token (firma, expiración)
    - Extraer user_id del payload
    - Buscar usuario en base de datos

    Retorna:
        Usuario autenticado

    Lanza:
        401 → token inválido, expirado, o usuario no existe
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        raise credentials_exception

    with UsuarioUnitOfWork() as uow:
        query = (
            select(Usuario)
            .where(Usuario.id == int(user_id), Usuario.deleted_at.is_(None))
            .options(selectinload(Usuario.roles))
        )
        user = uow.session.exec(query).first()

        if user is None or not user.is_active():
            raise credentials_exception

        return user


def require_role(allowed_roles: list[str]):
    """
    Factory de dependencias para control de acceso basado en roles (RBAC).

    Valida que el usuario autenticado tenga AL MENOS UNO de los roles
    especificados en allowed_roles.

    Uso típico:
        @router.get("/admin", dependencies=[Depends(require_role(["ADMIN"]))])

        @router.post("/productos")
        def crear_producto(
            _: Usuario = Depends(require_role(["ADMIN", "STOCK"])),
            ...
        ):
    """

    async def role_checker(
        current_user: Annotated[Usuario, Depends(get_current_user)],
    ) -> Usuario:
        user_role_codes = {rol.codigo for rol in current_user.roles}

        if not user_role_codes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes roles asignados",
            )

        if not any(role in user_role_codes for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Permisos insuficientes. Tu rol es '{next(iter(user_role_codes))}'. "
                    f"Se requiere uno de: {allowed_roles}"
                ),
            )

        return current_user

    return role_checker
