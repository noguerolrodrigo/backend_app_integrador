"""
Unit of Work contextual para el módulo de Usuario.

Cada módulo de dominio tiene su propio UoW que:
- Abre su propia sesión de base de datos
- Instancia solo los repositorios que ese módulo necesita
- Maneja automáticamente commit/rollback/close con context manager

Uso típico (dentro de un router):
    with UsuarioUnitOfWork() as uow:
        service = UsuarioService(uow)
        usuario = service.crear_usuario(data)
        # commit automático al salir del with
"""

from typing import Optional

from sqlmodel import Session

from app.core.database import engine
from app.modules.usuario.repository import (
    UsuarioRepository,
    RolRepository,
    UsuarioRolRepository,
)


class UsuarioUnitOfWork:
    """Unit of Work del módulo Usuario.

    Encapsula una transacción completa con sesión propia y los repos
    específicos del módulo (usuarios, roles, usuario_rol).

    El commit es automático al salir del context manager si no hubo
    excepciones. Si hubo, hace rollback automático.
    """

    def __init__(self, session: Optional[Session] = None):
        """Inicializa el UoW.

        Args:
            session: Si se provee, REUTILIZA esa sesión (útil cuando otro
                     módulo o el caller ya abrió la sesión). Si es None,
                     crea una propia que también cierra al salir.
        """
        self._external_session = session is not None
        self.session = session
        self.usuarios: Optional[UsuarioRepository] = None
        self.roles: Optional[RolRepository] = None
        self.usuarios_roles: Optional[UsuarioRolRepository] = None

    def _initialize_repos(self) -> None:
        """Inicializa los repositorios del módulo contra la sesión activa."""
        self.usuarios = UsuarioRepository(self.session)
        self.roles = RolRepository(self.session)
        self.usuarios_roles = UsuarioRolRepository(self.session)

    def __enter__(self) -> "UsuarioUnitOfWork":
        """Abre la sesión (si no vino dada) e instancia los repos del módulo."""
        if self.session is None:
            self.session = Session(engine, expire_on_commit=False)
        self._initialize_repos()
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[Exception],
        exc_tb: object,
    ) -> None:
        """Maneja automáticamente el cierre de la transacción.

        - Sin excepción → commit()
        - Con excepción → rollback()
        - Siempre → close() de la sesión (solo si fue creada internamente)
        """
        try:
            if exc_type is not None:
                self.session.rollback()
            else:
                self.session.commit()
        finally:
            if not self._external_session:
                self.session.close()
