import os
import secrets
import warnings
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    jwt_secret: str
    jwt_algorithm: str
    jwt_access_token_exp_minutes: int
    google_oauth_client_id: str
    google_oidc_jwks_url: str
    google_oidc_algorithm: str


def _load_settings() -> Settings:
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        # Keep local dev runnable while preventing a predictable shared fallback secret.
        jwt_secret = secrets.token_urlsafe(48)
        warnings.warn(
            "JWT_SECRET is not set; using an ephemeral process-local secret. "
            "Set JWT_SECRET explicitly for stable sessions and secure deployments.",
            stacklevel=2,
        )

    return Settings(
        jwt_secret=jwt_secret,
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        jwt_access_token_exp_minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXP_MINUTES", "60")),
        google_oauth_client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", ""),
        google_oidc_jwks_url=os.getenv(
            "GOOGLE_OIDC_JWKS_URL",
            "https://www.googleapis.com/oauth2/v3/certs",
        ),
        google_oidc_algorithm=os.getenv("GOOGLE_OIDC_ALGORITHM", "RS256"),
    )


settings = _load_settings()
