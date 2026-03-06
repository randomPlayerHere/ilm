from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Mapping, Protocol

import jwt
from jwt import PyJWKClient
from pydantic import BaseModel, ConfigDict, ValidationError

from app.core.settings import settings

GOOGLE_ISSUERS = {"accounts.google.com", "https://accounts.google.com"}


class InvalidGoogleClaimsError(Exception):
    pass


class InvalidGoogleTokenError(Exception):
    pass


class GoogleClaims(BaseModel):
    model_config = ConfigDict(extra="ignore")

    sub: str
    email: str
    email_verified: bool
    aud: str | list[str]
    iss: str
    exp: int


def validate_google_claims(
    raw_claims: Mapping[str, Any],
    *,
    client_id: str,
    now_ts: int | None = None,
) -> GoogleClaims:
    if not client_id:
        raise InvalidGoogleClaimsError("Google OAuth client ID is not configured")

    try:
        claims = GoogleClaims.model_validate(raw_claims)
    except ValidationError as exc:
        raise InvalidGoogleClaimsError("Google claims payload is invalid") from exc

    if claims.iss not in GOOGLE_ISSUERS:
        raise InvalidGoogleClaimsError("Google token issuer is invalid")

    audiences = claims.aud if isinstance(claims.aud, list) else [claims.aud]
    if client_id not in audiences:
        raise InvalidGoogleClaimsError("Google token audience is invalid")

    current_ts = now_ts if now_ts is not None else int(datetime.now(UTC).timestamp())
    if claims.exp <= current_ts:
        raise InvalidGoogleClaimsError("Google token is expired")

    if not claims.email_verified:
        raise InvalidGoogleClaimsError("Google account email is not verified")

    return claims.model_copy(update={"email": claims.email.strip().lower()})


class GoogleTokenVerifier(Protocol):
    def verify_id_token(self, id_token: str) -> GoogleClaims:
        ...


@dataclass
class GoogleJwksTokenVerifier:
    client_id: str
    jwks_url: str
    algorithm: str = "RS256"

    def __post_init__(self) -> None:
        self._jwks_client = PyJWKClient(self.jwks_url)

    def verify_id_token(self, id_token: str) -> GoogleClaims:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(id_token)
            raw_claims = jwt.decode(
                id_token,
                signing_key.key,
                algorithms=[self.algorithm],
                options={
                    "verify_aud": False,
                    "verify_exp": False,
                },
            )
        except Exception as exc:
            raise InvalidGoogleTokenError("Google token verification failed") from exc

        try:
            return validate_google_claims(raw_claims, client_id=self.client_id)
        except InvalidGoogleClaimsError as exc:
            raise InvalidGoogleTokenError("Google token verification failed") from exc


def build_default_google_verifier() -> GoogleTokenVerifier:
    return GoogleJwksTokenVerifier(
        client_id=settings.google_oauth_client_id,
        jwks_url=settings.google_oidc_jwks_url,
        algorithm=settings.google_oidc_algorithm,
    )
