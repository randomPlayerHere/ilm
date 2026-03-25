from __future__ import annotations

import asyncio

import httpx

from app.core.security import create_access_token
from app.domains.auth.google_oidc import GoogleClaims, GoogleTokenVerifier
from app.domains.auth.router import (
    get_google_token_verifier,
    reset_auth_state_for_tests,
)
from app.domains.onboarding.repository import InMemoryOnboardingRepository
from app.main import app


class StubVerifier(GoogleTokenVerifier):
    def __init__(self, token_to_claims: dict[str, GoogleClaims]) -> None:
        self._token_to_claims = token_to_claims

    def verify_id_token(self, id_token: str) -> GoogleClaims:
        if id_token not in self._token_to_claims:
            raise ValueError("invalid token")
        return self._token_to_claims[id_token]


def _admin_headers() -> dict[str, str]:
    access_token, _ = create_access_token(
        subject="usr_admin_1", org_id="org_demo_1", role="admin"
    )
    return {"Authorization": f"Bearer {access_token}"}


def setup_function():
    reset_auth_state_for_tests()
    InMemoryOnboardingRepository.reset_state()
    app.dependency_overrides.clear()


def _teacher_headers_for_consent_tests() -> dict[str, str]:
    token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="teacher"
    )
    return {"Authorization": f"Bearer {token}"}


def _parent_headers_for_consent_tests() -> dict[str, str]:
    token, _ = create_access_token(
        subject="usr_parent_1", org_id="org_demo_1", role="parent"
    )
    return {"Authorization": f"Bearer {token}"}


def test_create_org_success_and_duplicate_conflict():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            create = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Acme Schools", "slug": "acme-schools"},
            )
            assert create.status_code == 201
            body = create.json()
            assert body["name"] == "Acme Schools"
            assert body["slug"] == "acme-schools"
            assert body["org_id"].startswith("org_")
            assert body["membership_assignment_available"] is True

            duplicate = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Acme Schools 2", "slug": "acme-schools"},
            )
            assert duplicate.status_code == 409

    asyncio.run(scenario())


def test_admin_required_for_org_create():
    user_token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="teacher"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/admin/organizations",
                headers={"Authorization": f"Bearer {user_token}"},
                json={"name": "Blocked", "slug": "blocked"},
            )
            assert response.status_code == 403

    asyncio.run(scenario())


def test_inactive_admin_token_is_rejected_for_protected_admin_endpoints():
    admin_token, _ = create_access_token(
        subject="usr_admin_1", org_id="org_demo_1", role="admin"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            deactivated = await client.post(
                "/admin/users/usr_admin_1/deactivate",
                headers=_admin_headers(),
            )
            assert deactivated.status_code == 200

            rejected = await client.post(
                "/admin/organizations",
                headers={"Authorization": f"Bearer {admin_token}"},
                json={"name": "Should Fail", "slug": "should-fail"},
            )
            assert rejected.status_code == 403

    asyncio.run(scenario())


def test_unknown_admin_subject_in_token_is_rejected():
    unknown_admin, _ = create_access_token(
        subject="usr_missing_admin", org_id="org_demo_1", role="admin"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/admin/organizations",
                headers={"Authorization": f"Bearer {unknown_admin}"},
                json={"name": "Ghost", "slug": "ghost"},
            )
            assert response.status_code == 403

    asyncio.run(scenario())


def test_invite_accept_and_lifecycle_transitions_with_auth_regression_guards():
    verifier = StubVerifier(
        {
            "active-teacher-google-token-32-plus": GoogleClaims(
                sub="google-sub-teacher-1",
                email="teacher@example.com",
                email_verified=True,
                aud="test-google-client-id",
                iss="https://accounts.google.com",
                exp=4_000_000_000,
            )
        }
    )

    async def override_verifier():
        return verifier

    app.dependency_overrides[get_google_token_verifier] = override_verifier

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            create_org = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Delta Academy", "slug": "delta-academy"},
            )
            org_id = create_org.json()["org_id"]

            invite = await client.post(
                "/admin/users/invite",
                headers=_admin_headers(),
                json={
                    "email": "new.admin@example.com",
                    "role": "admin",
                    "org_id": org_id,
                    "expires_in_seconds": 3600,
                },
            )
            assert invite.status_code == 201
            invite_body = invite.json()
            assert invite_body["status"] == "invited"
            assert invite_body["org_id"] == org_id

            accepted = await client.post(
                "/admin/invitations/accept",
                json={
                    "invitation_token": invite_body["invitation_token"],
                    "org_id": org_id,
                },
            )
            assert accepted.status_code == 200
            accepted_body = accepted.json()
            assert accepted_body["status"] == "active"
            assert accepted_body["org_id"] == org_id

            deactivate = await client.post(
                "/admin/users/usr_teacher_1/deactivate",
                headers=_admin_headers(),
            )
            assert deactivate.status_code == 200

            email_login = await client.post(
                "/auth/login",
                json={
                    "email": "teacher@example.com",
                    "password": "correct-horse-battery-staple",
                },
            )
            assert email_login.status_code == 401
            assert email_login.json() == {"detail": "Invalid credentials"}

            google_login = await client.post(
                "/auth/google",
                json={"id_token": "active-teacher-google-token-32-plus"},
            )
            assert google_login.status_code == 401
            assert google_login.json() == {"detail": "Google authentication failed"}

            activate = await client.post(
                "/admin/users/usr_teacher_1/activate",
                headers=_admin_headers(),
            )
            assert activate.status_code == 200
            assert activate.json()["status"] == "active"

    asyncio.run(scenario())


def test_invitation_fail_closed_cases():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            create_org = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Beta Academy", "slug": "beta-academy"},
            )
            org_id = create_org.json()["org_id"]

            invite = await client.post(
                "/admin/users/invite",
                headers=_admin_headers(),
                json={
                    "email": "pending.user@example.com",
                    "role": "teacher",
                    "org_id": org_id,
                    "expires_in_seconds": 0,
                },
            )
            assert invite.status_code == 201
            token = invite.json()["invitation_token"]

            expired = await client.post(
                "/admin/invitations/accept",
                json={"invitation_token": token, "org_id": org_id},
            )
            assert expired.status_code == 400

            valid_invite = await client.post(
                "/admin/users/invite",
                headers=_admin_headers(),
                json={
                    "email": "pending.user2@example.com",
                    "role": "teacher",
                    "org_id": org_id,
                    "expires_in_seconds": 3600,
                },
            )
            valid_token = valid_invite.json()["invitation_token"]

            wrong_org = await client.post(
                "/admin/invitations/accept",
                json={"invitation_token": valid_token, "org_id": "org_wrong"},
            )
            assert wrong_org.status_code == 403

            first_accept = await client.post(
                "/admin/invitations/accept",
                json={"invitation_token": valid_token, "org_id": org_id},
            )
            assert first_accept.status_code == 200

            replay = await client.post(
                "/admin/invitations/accept",
                json={"invitation_token": valid_token, "org_id": org_id},
            )
            assert replay.status_code == 400

    asyncio.run(scenario())


def test_activate_unknown_user_returns_not_found():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/admin/users/usr_does_not_exist/activate",
                headers=_admin_headers(),
            )
            assert response.status_code == 404

    asyncio.run(scenario())


def test_assign_role_success_and_unsupported_role_rejected():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            update = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "principal"},
            )
            assert update.status_code == 200
            assert update.json()["role"] == "principal"

            invalid = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "superuser"},
            )
            assert invalid.status_code == 400

    asyncio.run(scenario())


def test_assign_membership_and_cross_tenant_protected_access_fail_closed():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            promote = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "principal"},
            )
            assert promote.status_code == 200
            principal_token, _ = create_access_token(
                subject="usr_teacher_1", org_id="org_demo_1", role="principal"
            )

            new_org = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Tenant Two", "slug": "tenant-two"},
            )
            new_org_id = new_org.json()["org_id"]

            membership = await client.post(
                "/admin/users/usr_teacher_1/membership",
                headers=_admin_headers(),
                json={"org_id": new_org_id},
            )
            assert membership.status_code == 200
            assert membership.json()["org_id"] == new_org_id

            wrong_tenant = await client.get(
                f"/admin/protected/organizations/org_demo_1/summary",
                headers={"Authorization": f"Bearer {principal_token}"},
            )
            assert wrong_tenant.status_code == 403
            body = wrong_tenant.json()
            assert body == {"detail": "Forbidden"}

            principal_new_org_token, _ = create_access_token(
                subject="usr_teacher_1",
                org_id=new_org_id,
                role="principal",
            )
            allowed = await client.get(
                f"/admin/protected/organizations/{new_org_id}/summary",
                headers={"Authorization": f"Bearer {principal_new_org_token}"},
            )
            assert allowed.status_code == 200
            assert allowed.json()["org_id"] == new_org_id

    asyncio.run(scenario())


def test_protected_operations_require_auth_and_role_checks():
    teacher_token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="teacher"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            unauth = await client.get(
                "/admin/protected/organizations/org_demo_1/summary"
            )
            assert unauth.status_code == 401

            forbidden = await client.get(
                "/admin/protected/organizations/org_demo_1/summary",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )
            assert forbidden.status_code == 403

            promote = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "principal"},
            )
            assert promote.status_code == 200
            principal_token, _ = create_access_token(
                subject="usr_teacher_1", org_id="org_demo_1", role="principal"
            )

            allowed = await client.get(
                "/admin/protected/organizations/org_demo_1/summary",
                headers={"Authorization": f"Bearer {principal_token}"},
            )
            assert allowed.status_code == 200

    asyncio.run(scenario())


def test_protected_operations_reject_invalid_jwt():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.get(
                "/admin/protected/organizations/org_demo_1/summary",
                headers={"Authorization": "Bearer not-a-valid-jwt"},
            )
            assert response.status_code == 401
            assert response.json() == {"detail": "Authentication required"}

    asyncio.run(scenario())


def test_stale_principal_token_is_rejected_after_role_downgrade():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            promote = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "principal"},
            )
            assert promote.status_code == 200
            principal_token, _ = create_access_token(
                subject="usr_teacher_1", org_id="org_demo_1", role="principal"
            )

            demote = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers=_admin_headers(),
                json={"role": "teacher"},
            )
            assert demote.status_code == 200

            stale = await client.get(
                "/admin/protected/organizations/org_demo_1/summary",
                headers={"Authorization": f"Bearer {principal_token}"},
            )
            assert stale.status_code == 403
            assert stale.json() == {"detail": "Forbidden"}

    asyncio.run(scenario())


def test_admin_operations_reject_token_without_org_scope():
    no_org_token, _ = create_access_token(
        subject="usr_admin_1", org_id="", role="admin"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            response = await client.post(
                "/admin/users/usr_teacher_1/role",
                headers={"Authorization": f"Bearer {no_org_token}"},
                json={"role": "principal"},
            )
            assert response.status_code == 401
            assert response.json() == {"detail": "Authentication required"}

    asyncio.run(scenario())


def test_safety_controls_admin_update_and_read_with_versioning():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            created = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                headers=_admin_headers(),
                json={
                    "moderation_mode": "balanced",
                    "blocked_categories": ["violence", "self-harm"],
                    "age_safety_level": "standard",
                    "max_response_tone": "neutral",
                },
            )
            assert created.status_code == 200
            assert created.json()["version"] == 1

            updated = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                headers=_admin_headers(),
                json={
                    "moderation_mode": "strict",
                    "blocked_categories": ["hate"],
                    "age_safety_level": "enhanced",
                    "max_response_tone": "supportive",
                },
            )
            assert updated.status_code == 200
            assert updated.json()["version"] == 2

            fetched = await client.get(
                "/admin/organizations/org_demo_1/safety-controls",
                headers=_admin_headers(),
            )
            assert fetched.status_code == 200
            body = fetched.json()
            assert body["version"] == 2
            assert body["moderation_mode"] == "strict"
            assert body["blocked_categories"] == ["hate"]

    asyncio.run(scenario())


def test_safety_controls_reject_non_admin_unauthenticated_and_cross_tenant():
    teacher_token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="teacher"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            unauthenticated = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                json={
                    "moderation_mode": "balanced",
                    "blocked_categories": ["violence"],
                    "age_safety_level": "standard",
                    "max_response_tone": "neutral",
                },
            )
            assert unauthenticated.status_code == 401

            non_admin = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={
                    "moderation_mode": "balanced",
                    "blocked_categories": ["violence"],
                    "age_safety_level": "standard",
                    "max_response_tone": "neutral",
                },
            )
            assert non_admin.status_code == 403

            create_other_org = await client.post(
                "/admin/organizations",
                headers=_admin_headers(),
                json={"name": "Org Three", "slug": "org-three"},
            )
            assert create_other_org.status_code == 201
            other_org_id = create_other_org.json()["org_id"]

            cross_tenant_update = await client.put(
                f"/admin/organizations/{other_org_id}/safety-controls",
                headers=_admin_headers(),
                json={
                    "moderation_mode": "strict",
                    "blocked_categories": ["hate"],
                    "age_safety_level": "enhanced",
                    "max_response_tone": "supportive",
                },
            )
            assert cross_tenant_update.status_code == 403
            assert cross_tenant_update.json() == {"detail": "Forbidden"}

            cross_tenant_read = await client.get(
                f"/admin/organizations/{other_org_id}/safety-controls",
                headers=_admin_headers(),
            )
            assert cross_tenant_read.status_code == 403
            assert cross_tenant_read.json() == {"detail": "Forbidden"}

    asyncio.run(scenario())


def test_safety_controls_noop_update_rejected_and_student_read_denied():
    student_token, _ = create_access_token(
        subject="usr_teacher_1", org_id="org_demo_1", role="student"
    )

    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            first = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                headers=_admin_headers(),
                json={
                    "moderation_mode": "balanced",
                    "blocked_categories": ["violence"],
                    "age_safety_level": "standard",
                    "max_response_tone": "neutral",
                },
            )
            assert first.status_code == 200

            noop = await client.put(
                "/admin/organizations/org_demo_1/safety-controls",
                headers=_admin_headers(),
                json={
                    "moderation_mode": "balanced",
                    "blocked_categories": ["violence"],
                    "age_safety_level": "standard",
                    "max_response_tone": "neutral",
                },
            )
            assert noop.status_code == 400
            assert noop.json() == {"detail": "No changes detected in safety controls"}

            denied_read = await client.get(
                "/admin/organizations/org_demo_1/safety-controls",
                headers={"Authorization": f"Bearer {student_token}"},
            )
            assert denied_read.status_code == 403
            assert denied_read.json() == {"detail": "Forbidden"}

    asyncio.run(scenario())


# ─── COPPA consent ────────────────────────────────────────────────────────────


def test_confirm_consent_success():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Young Student", "grade_level": "Grade 5"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 200
            body = confirm.json()
            assert body["consent_status"] == "confirmed"
            assert body["confirmed_by"] == "usr_admin_1"
            assert body["student_id"] == student_id
            assert "confirmed_at" in body

    asyncio.run(scenario())


def test_confirm_consent_not_required_raises_409():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Older Student", "grade_level": "Grade 10"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 409

    asyncio.run(scenario())


def test_confirm_consent_already_confirmed_raises_409():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Minor Student", "grade_level": "Grade 3"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            first = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert first.status_code == 200

            second = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert second.status_code == 409

    asyncio.run(scenario())


def test_confirm_consent_wrong_org_forbidden():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Child Student", "grade_level": "Grade 2"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            # Admin from org_demo_1 attempts to confirm for org_demo_2
            confirm = await client.post(
                f"/admin/organizations/org_demo_2/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 403

    asyncio.run(scenario())


def test_confirm_consent_non_admin_forbidden():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Young One", "grade_level": "Grade 1"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            teacher_confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_teacher_headers_for_consent_tests(),
            )
            assert teacher_confirm.status_code == 403

            parent_confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_parent_headers_for_consent_tests(),
            )
            assert parent_confirm.status_code == 403

    asyncio.run(scenario())


def test_list_pending_consent_returns_under_13_only():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            teacher_hdrs = _teacher_headers_for_consent_tests()
            await client.post(
                "/onboarding/classes/cls_1/students",
                headers=teacher_hdrs,
                json={"name": "Grade5 Student", "grade_level": "Grade 5"},
            )
            await client.post(
                "/onboarding/classes/cls_1/students",
                headers=teacher_hdrs,
                json={"name": "KinderStudent", "grade_level": "Kindergarten"},
            )
            await client.post(
                "/onboarding/classes/cls_1/students",
                headers=teacher_hdrs,
                json={"name": "HighSchooler", "grade_level": "Grade 10"},
            )

            resp = await client.get(
                "/admin/organizations/org_demo_1/students/pending-consent",
                headers=_admin_headers(),
            )
            assert resp.status_code == 200
            body = resp.json()
            assert len(body["students"]) == 2
            statuses = {s["consent_status"] for s in body["students"]}
            assert statuses == {"pending"}

    asyncio.run(scenario())


def test_confirm_consent_removes_from_pending_list():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Grade5 Kid", "grade_level": "Grade 5"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 200

            resp = await client.get(
                "/admin/organizations/org_demo_1/students/pending-consent",
                headers=_admin_headers(),
            )
            assert resp.status_code == 200
            assert resp.json()["students"] == []

    asyncio.run(scenario())


def test_get_student_consent_record_returns_auditable_fields_after_confirmation():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Auditable Minor", "grade_level": "Grade 4"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            confirm = await client.post(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert confirm.status_code == 200

            consent_record = await client.get(
                f"/admin/organizations/org_demo_1/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert consent_record.status_code == 200
            body = consent_record.json()
            assert body["student_id"] == student_id
            assert body["org_id"] == "org_demo_1"
            assert body["consent_status"] == "confirmed"
            assert body["confirmed_by"] == "usr_admin_1"
            assert body["confirmed_at"] is not None

    asyncio.run(scenario())


def test_get_student_consent_record_wrong_org_forbidden():
    async def scenario():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            student_resp = await client.post(
                "/onboarding/classes/cls_1/students",
                headers=_teacher_headers_for_consent_tests(),
                json={"name": "Cross Org Child", "grade_level": "Grade 5"},
            )
            assert student_resp.status_code == 201
            student_id = student_resp.json()["student_id"]

            resp = await client.get(
                f"/admin/organizations/org_demo_2/students/{student_id}/consent",
                headers=_admin_headers(),
            )
            assert resp.status_code == 403

    asyncio.run(scenario())
