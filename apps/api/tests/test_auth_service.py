import pytest

from app.core.security import decode_token, hash_password
from app.domains.auth.google_oidc import GoogleClaims
from app.domains.auth.models import UserRecord
from app.domains.auth.service import AuthService, InvalidCredentialsError, NoAuthorizedMembershipError


class StubRepo:
    def __init__(self, users):
        self._users = users

    def get_by_email(self, normalized_email: str):
        return self._users.get(normalized_email)

    def get_by_google_sub(self, google_sub: str):
        for user in self._users.values():
            if user.google_sub == google_sub:
                return user
        return None

    def link_google_sub(self, user_id: str, google_sub: str) -> None:
        for email, user in self._users.items():
            if user.user_id != user_id:
                continue
            self._users[email] = UserRecord(
                user_id=user.user_id,
                org_id=user.org_id,
                email=user.email,
                password_hash=user.password_hash,
                role=user.role,
                status=user.status,
                google_sub=google_sub,
            )
            return


def _active_teacher() -> UserRecord:
    return UserRecord(
        user_id="usr_1",
        org_id="org_1",
        email="teacher@example.com",
        password_hash=hash_password("correct-horse-battery-staple"),
        role="teacher",
        status="active",
    )


def _google_claims(**overrides) -> GoogleClaims:
    base = {
        "sub": "google-sub-teacher-1",
        "email": "teacher@example.com",
        "email_verified": True,
        "aud": "test-google-client-id",
        "iss": "https://accounts.google.com",
        "exp": 4_000_000_000,
    }
    base.update(overrides)
    return GoogleClaims(**base)


def test_login_success_includes_role_and_org_in_token():
    repo = StubRepo({"teacher@example.com": _active_teacher()})
    service = AuthService(repository=repo)

    result = service.login_with_email_password("Teacher@Example.com", "correct-horse-battery-staple")
    payload = decode_token(result.access_token)

    assert result.role == "teacher"
    assert result.org_id == "org_1"
    assert payload["sub"] == "usr_1"
    assert payload["role"] == "teacher"
    assert payload["org_id"] == "org_1"
    assert payload["exp"] > 0


def test_login_unknown_user_is_generic_failure():
    service = AuthService(repository=StubRepo({}))
    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_email_password("unknown@example.com", "whatever-password")


def test_login_inactive_user_is_generic_failure():
    inactive = _active_teacher()
    inactive = UserRecord(
        user_id=inactive.user_id,
        org_id=inactive.org_id,
        email=inactive.email,
        password_hash=inactive.password_hash,
        role=inactive.role,
        status="inactive",
    )
    service = AuthService(repository=StubRepo({"teacher@example.com": inactive}))
    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_email_password("teacher@example.com", "correct-horse-battery-staple")


def test_login_wrong_password_is_generic_failure():
    service = AuthService(repository=StubRepo({"teacher@example.com": _active_teacher()}))
    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_email_password("teacher@example.com", "wrong-password-value")


def test_login_with_unknown_role_is_generic_failure():
    invalid_role_user = UserRecord(
        user_id="usr_2",
        org_id="org_1",
        email="rogue@example.com",
        password_hash=hash_password("correct-horse-battery-staple"),
        role="superuser",
        status="active",
    )
    service = AuthService(repository=StubRepo({"rogue@example.com": invalid_role_user}))
    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_email_password("rogue@example.com", "correct-horse-battery-staple")


def test_google_login_success_by_google_sub_reuses_session_contract():
    teacher = UserRecord(
        user_id="usr_1",
        org_id="org_1",
        email="teacher@example.com",
        password_hash=hash_password("irrelevant-for-google"),
        role="teacher",
        status="active",
        google_sub="google-sub-teacher-1",
    )
    service = AuthService(repository=StubRepo({"teacher@example.com": teacher}))

    result = service.login_with_google_claims(_google_claims())
    payload = decode_token(result.access_token)

    assert result.role == "teacher"
    assert result.org_id == "org_1"
    assert payload["sub"] == "usr_1"
    assert payload["role"] == "teacher"
    assert payload["org_id"] == "org_1"


def test_google_login_maps_by_email_then_links_google_sub():
    teacher = UserRecord(
        user_id="usr_1",
        org_id="org_1",
        email="teacher@example.com",
        password_hash=hash_password("irrelevant-for-google"),
        role="teacher",
        status="active",
        google_sub=None,
    )
    repo = StubRepo({"teacher@example.com": teacher})
    service = AuthService(repository=repo)

    service.login_with_google_claims(_google_claims(sub="new-google-sub"))

    assert repo.get_by_google_sub("new-google-sub") is not None


def test_google_login_rejects_rebinding_when_existing_google_sub_differs():
    teacher = UserRecord(
        user_id="usr_1",
        org_id="org_1",
        email="teacher@example.com",
        password_hash=hash_password("irrelevant-for-google"),
        role="teacher",
        status="active",
        google_sub="existing-google-sub",
    )
    service = AuthService(repository=StubRepo({"teacher@example.com": teacher}))

    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_google_claims(_google_claims(sub="different-google-sub"))


def test_google_login_without_authorized_membership_is_denied_with_contact_admin_message():
    service = AuthService(repository=StubRepo({}))

    with pytest.raises(NoAuthorizedMembershipError, match="authorized organization membership"):
        service.login_with_google_claims(_google_claims(email="not-member@example.com", sub="unknown-sub"))


def test_google_login_with_unsupported_role_is_generic_failure():
    unsupported = UserRecord(
        user_id="usr_2",
        org_id="org_1",
        email="rogue@example.com",
        password_hash=hash_password("irrelevant-for-google"),
        role="superuser",
        status="active",
        google_sub="google-sub-rogue",
    )
    service = AuthService(repository=StubRepo({"rogue@example.com": unsupported}))

    with pytest.raises(InvalidCredentialsError, match="Invalid credentials"):
        service.login_with_google_claims(
            _google_claims(
                sub="google-sub-rogue",
                email="rogue@example.com",
            )
        )
