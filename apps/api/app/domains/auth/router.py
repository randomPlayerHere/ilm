from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import InMemoryLoginRateLimiter
from app.domains.auth.google_oidc import (
    GoogleTokenVerifier,
    InvalidGoogleTokenError,
    build_default_google_verifier,
)
from app.domains.auth.repository import InMemoryAuthRepository
from app.domains.auth.schemas import GoogleLoginRequest, LoginRequest, LoginResponse
from app.domains.auth.service import AuthService, InvalidCredentialsError, NoAuthorizedMembershipError

router = APIRouter(prefix="/auth", tags=["auth"])

_auth_service = AuthService(repository=InMemoryAuthRepository())
_google_verifier: GoogleTokenVerifier | None = None
_login_rate_limiter = InMemoryLoginRateLimiter()


def check_login_rate_limit(email: str) -> None:
    if _login_rate_limiter.is_limited(email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )


def reset_login_rate_limiter_for_tests() -> None:
    _login_rate_limiter.clear()


def reset_auth_state_for_tests() -> None:
    InMemoryAuthRepository.reset_state()
    _login_rate_limiter.clear()


async def get_auth_service() -> AuthService:
    return _auth_service


async def get_google_token_verifier() -> GoogleTokenVerifier:
    global _google_verifier
    if _google_verifier is None:
        _google_verifier = build_default_google_verifier()
    return _google_verifier


@router.post("/login", response_model=LoginResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    check_login_rate_limit(payload.email)
    try:
        auth = service.login_with_email_password(payload.email, payload.password)
    except InvalidCredentialsError as exc:
        _login_rate_limiter.record_failure(payload.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        ) from exc
    _login_rate_limiter.record_success(payload.email)
    return LoginResponse.from_auth(
        access_token=auth.access_token,
        expires_in=auth.expires_in,
        role=auth.role,
        org_id=auth.org_id,
    )


@router.post("/google", response_model=LoginResponse)
async def login_with_google(
    payload: GoogleLoginRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
    verifier: GoogleTokenVerifier = Depends(get_google_token_verifier),
) -> LoginResponse:
    client_host = request.client.host if request.client else "unknown-client"
    unknown_key = f"google-invalid:{client_host}"
    check_login_rate_limit(unknown_key)

    try:
        claims = verifier.verify_id_token(payload.id_token)
    except (InvalidGoogleTokenError, ValueError) as exc:
        _login_rate_limiter.record_failure(unknown_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        ) from exc

    user_key = f"google:{claims.email}"
    check_login_rate_limit(user_key)

    try:
        auth = service.login_with_google_claims(claims)
    except NoAuthorizedMembershipError as exc:
        _login_rate_limiter.record_failure(user_key)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except InvalidCredentialsError as exc:
        _login_rate_limiter.record_failure(user_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google authentication failed",
        ) from exc

    _login_rate_limiter.record_success(unknown_key)
    _login_rate_limiter.record_success(user_key)
    return LoginResponse.from_auth(
        access_token=auth.access_token,
        expires_in=auth.expires_in,
        role=auth.role,
        org_id=auth.org_id,
    )
