from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    nombre: str
    apellido: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: int
    email: str
    nombre: str
    apellido: str
    roles: list[str]


class LoginResponse(BaseModel):
    """Respuesta para endpoints que no emiten nuevos tokens (GET /me)."""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    nombre: str
    apellido: str
    roles: list[str]


class TokenData(BaseModel):
    user_id: int
    email: str
    roles: list[str]


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str
