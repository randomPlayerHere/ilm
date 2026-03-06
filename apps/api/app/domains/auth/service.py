from __future__ import annotations

from dataclasses import dataclass

from app.core.roles import is_supported_role
from app.core.security import create_access_token, verify_password
from app.domains.auth.google_oidc import GoogleClaims
from app.domains.auth.repository import AuthRepository


class InvalidCredentialsError(Exception):
    pass


class NoAuthorizedMembershipError(Exception):
    pass


@dataclass(frozen=True)
class AuthSuccess:
    access_token: str
    expires_in: int
    role: str
    org_id: str


class AuthService:
    def __init__(self, repository: AuthRepository) -> None:
        self._repository = repository

    def login_with_email_password(self, email: str, password: str) -> AuthSuccess:
        normalized_email = email.strip().lower()
        user = self._repository.get_by_email(normalized_email)
        if not user:
            raise InvalidCredentialsError("Invalid credentials")
        if user.status != "active":
            raise InvalidCredentialsError("Invalid credentials")
        if not is_supported_role(user.role):
            raise InvalidCredentialsError("Invalid credentials")
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")

        access_token, expires_in = create_access_token(
            subject=user.user_id,
            org_id=user.org_id,
            role=user.role,
        )
        return AuthSuccess(
            access_token=access_token,
            expires_in=expires_in,
            role=user.role,
            org_id=user.org_id,
        )

    def login_with_google_claims(self, claims: GoogleClaims) -> AuthSuccess:
        user = self._repository.get_by_google_sub(claims.sub)
        if user is None:
            user = self._repository.get_by_email(claims.email)
            if user is not None:
                if user.google_sub is not None and user.google_sub != claims.sub:
                    raise InvalidCredentialsError("Invalid credentials")
                self._repository.link_google_sub(user.user_id, claims.sub)
        if user is None:
            raise NoAuthorizedMembershipError(
                "Access requires an authorized organization membership. Please contact your administrator."
            )
        if user.status != "active":
            raise InvalidCredentialsError("Invalid credentials")
        if not is_supported_role(user.role):
            raise InvalidCredentialsError("Invalid credentials")

        access_token, expires_in = create_access_token(
            subject=user.user_id,
            org_id=user.org_id,
            role=user.role,
        )
        return AuthSuccess(
            access_token=access_token,
            expires_in=expires_in,
            role=user.role,
            org_id=user.org_id,
        )
