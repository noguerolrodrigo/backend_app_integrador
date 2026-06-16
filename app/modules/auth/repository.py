from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.modules.auth.model import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, token: str, user_id: int, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(token=token, user_id=user_id, expires_at=expires_at)
        self.session.add(rt)
        self.session.flush()
        return rt

    def get_by_token(self, token: str) -> Optional[RefreshToken]:
        return self.session.exec(
            select(RefreshToken).where(RefreshToken.token == token)
        ).first()

    def revoke(self, token: str) -> bool:
        rt = self.get_by_token(token)
        if not rt:
            return False
        rt.revoked_at = datetime.utcnow()
        self.session.add(rt)
        self.session.flush()
        return True

    def revoke_all_for_user(self, user_id: int) -> int:
        tokens = self.session.exec(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        ).all()
        now = datetime.utcnow()
        for t in tokens:
            t.revoked_at = now
            self.session.add(t)
        self.session.flush()
        return len(tokens)
