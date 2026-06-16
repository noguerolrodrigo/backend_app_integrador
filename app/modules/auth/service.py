from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlmodel import select

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.modules.auth.schemas import RegisterRequest, TokenResponse
from app.modules.auth.uow import AuthUnitOfWork
from app.modules.usuario.models import Usuario


class AuthService:
    def __init__(self, uow: AuthUnitOfWork):
        self.uow = uow

    def _load_user_with_roles(self, user_id: int) -> Usuario:
        stmt = (
            select(Usuario)
            .where(Usuario.id == user_id)
            .options(selectinload(Usuario.roles))
        )
        return self.uow.session.exec(stmt).first()

    def _build_token_response(self, user: Usuario) -> TokenResponse:
        role_codes = [rol.codigo for rol in user.roles]
        access_token = create_access_token(
            {"user_id": user.id, "email": user.email, "roles": role_codes}
        )
        expires_at = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
        refresh_token = create_refresh_token({"user_id": user.id, "email": user.email})
        self.uow.refresh_tokens.create(refresh_token, user.id, expires_at)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=user.id,
            email=user.email,
            nombre=user.nombre,
            apellido=user.apellido,
            roles=role_codes,
        )

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.uow.usuarios.get_by_email(email)
        if not user or not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )
        if not verify_password(password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email o contraseña incorrectos",
            )
        user = self._load_user_with_roles(user.id)
        return self._build_token_response(user)

    def register(self, data: RegisterRequest) -> TokenResponse:
        if self.uow.usuarios.exists_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El email {data.email} ya está registrado",
            )
        usuario = Usuario(
            email=data.email,
            nombre=data.nombre,
            apellido=data.apellido,
            password_hash=hash_password(data.password),
            activo=True,
        )
        self.uow.usuarios.create(usuario)

        rol_client = self.uow.roles.get_by_codigo("CLIENT")
        if rol_client:
            try:
                self.uow.usuarios_roles.asignar_rol(usuario.id, rol_client.id)
            except ValueError:
                pass

        user = self._load_user_with_roles(usuario.id)
        return self._build_token_response(user)

    def refresh(self, refresh_token_str: str) -> TokenResponse:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido",
            )
        rt = self.uow.refresh_tokens.get_by_token(refresh_token_str)
        if not rt:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no encontrado",
            )
        if rt.revoked_at is not None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token revocado",
            )
        if rt.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expirado",
            )
        user = self._load_user_with_roles(rt.user_id)
        if not user or not user.is_active():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario inactivo o eliminado",
            )
        role_codes = [rol.codigo for rol in user.roles]
        access_token = create_access_token(
            {"user_id": user.id, "email": user.email, "roles": role_codes}
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str,
            expires_in=settings.access_token_expire_minutes * 60,
            user_id=user.id,
            email=user.email,
            nombre=user.nombre,
            apellido=user.apellido,
            roles=role_codes,
        )

    def logout(self, refresh_token_str: str) -> None:
        self.uow.refresh_tokens.revoke(refresh_token_str)
