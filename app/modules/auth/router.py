from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_user
from app.core.rate_limit import check_rate_limit, record_failed_attempt
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.modules.auth.service import AuthService
from app.modules.auth.uow import AuthUnitOfWork
from app.modules.usuario.models import Usuario

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: Request, data: LoginRequest):
    ip = request.client.host
    is_limited, retry_after = check_rate_limit(ip)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        with AuthUnitOfWork() as uow:
            return AuthService(uow).login(data.email, data.password)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            record_failed_attempt(ip)
        raise


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: Request, data: RegisterRequest):
    ip = request.client.host
    is_limited, retry_after = check_rate_limit(ip)
    if is_limited:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Demasiados intentos fallidos. Intente más tarde.",
            headers={"Retry-After": str(retry_after)},
        )
    try:
        with AuthUnitOfWork() as uow:
            return AuthService(uow).register(data)
    except HTTPException as exc:
        if exc.status_code in (status.HTTP_409_CONFLICT, status.HTTP_400_BAD_REQUEST):
            record_failed_attempt(ip)
        raise


@router.post("/refresh", response_model=TokenResponse)
def refresh(data: RefreshRequest):
    with AuthUnitOfWork() as uow:
        return AuthService(uow).refresh(data.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(data: LogoutRequest, current_user: Usuario = Depends(get_current_user)):
    with AuthUnitOfWork() as uow:
        AuthService(uow).logout(data.refresh_token)


@router.get("/me", response_model=LoginResponse)
def get_me(current_user: Usuario = Depends(get_current_user)):
    role_codes = [rol.codigo for rol in current_user.roles]
    return LoginResponse(
        access_token="",
        user_id=current_user.id,
        email=current_user.email,
        nombre=current_user.nombre,
        apellido=current_user.apellido,
        roles=role_codes,
    )


@router.get("/verify")
def verify_token(current_user: Usuario = Depends(get_current_user)):
    role_codes = [rol.codigo for rol in current_user.roles]
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "roles": role_codes,
    }
