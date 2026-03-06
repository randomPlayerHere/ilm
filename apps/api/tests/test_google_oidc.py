from __future__ import annotations

import pytest

from app.domains.auth.google_oidc import InvalidGoogleClaimsError, validate_google_claims


def _claims(**overrides):
    base = {
        "sub": "sub-1",
        "email": "Teacher@Example.com",
        "email_verified": True,
        "aud": "google-client-id",
        "iss": "https://accounts.google.com",
        "exp": 4_000_000_000,
    }
    base.update(overrides)
    return base


def test_validate_google_claims_accepts_valid_claims_and_normalizes_email():
    claims = validate_google_claims(_claims(), client_id="google-client-id", now_ts=1_000)

    assert claims.sub == "sub-1"
    assert claims.email == "teacher@example.com"


@pytest.mark.parametrize("iss", ["accounts.google.com", "https://accounts.google.com"])
def test_validate_google_claims_accepts_google_issuers(iss: str):
    claims = validate_google_claims(_claims(iss=iss), client_id="google-client-id", now_ts=1_000)

    assert claims.iss == iss


def test_validate_google_claims_rejects_wrong_issuer():
    with pytest.raises(InvalidGoogleClaimsError, match="issuer"):
        validate_google_claims(_claims(iss="https://evil.example.com"), client_id="google-client-id", now_ts=1_000)


def test_validate_google_claims_rejects_wrong_audience():
    with pytest.raises(InvalidGoogleClaimsError, match="audience"):
        validate_google_claims(_claims(aud="some-other-client"), client_id="google-client-id", now_ts=1_000)


def test_validate_google_claims_rejects_expired_token():
    with pytest.raises(InvalidGoogleClaimsError, match="expired"):
        validate_google_claims(_claims(exp=500), client_id="google-client-id", now_ts=1_000)


def test_validate_google_claims_rejects_unverified_email():
    with pytest.raises(InvalidGoogleClaimsError, match="email"):
        validate_google_claims(_claims(email_verified=False), client_id="google-client-id", now_ts=1_000)
