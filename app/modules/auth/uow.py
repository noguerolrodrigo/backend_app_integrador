from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.auth.repository import RefreshTokenRepository
from app.modules.usuario.repository import RolRepository, UsuarioRepository, UsuarioRolRepository


class AuthUnitOfWork:
    def __init__(self, session: Optional[Session] = None):
        self._external_session = session is not None
        self.session = session
        self.refresh_tokens: Optional[RefreshTokenRepository] = None
        self.usuarios: Optional[UsuarioRepository] = None
        self.roles: Optional[RolRepository] = None
        self.usuarios_roles: Optional[UsuarioRolRepository] = None

    def __enter__(self) -> "AuthUnitOfWork":
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        self.usuarios = UsuarioRepository(self.session)
        self.roles = RolRepository(self.session)
        self.usuarios_roles = UsuarioRolRepository(self.session)
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: object) -> None:
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            if not self._external_session:
                self.session.close()
