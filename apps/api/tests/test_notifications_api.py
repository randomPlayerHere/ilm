from __future__ import annotations

import asyncio
import time

import httpx

from app.core.security import create_access_token
from app.domains.auth.router import reset_auth_state_for_tests
from app.domains.notifications.repository import (
    InMemoryNotificationPreferencesRepository,
    reset_notifications_state_for_tests,
)
from app.main import app


# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _parent_headers(user_id: str = "usr_parent_1", org_id: str = "org_demo_1") -> dict[str, str]:
    token, _ = create_access_token(subject=user_id, org_id=org_id, role="parent")
    return {"Authorization": f"Bearer {token}"}


def _student_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_student_1", org_id="org_demo_1", role="student")
    return {"Authorization": f"Bearer {token}"}


def _teacher_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_teacher_1", org_id="org_demo_1", role="teacher")
    return {"Authorization": f"Bearer {token}"}


def _admin_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_admin_1", org_id="org_demo_1", role="admin")
    return {"Authorization": f"Bearer {token}"}


def _principal_headers() -> dict[str, str]:
    token, _ = create_access_token(subject="usr_principal_1", org_id="org_demo_1", role="principal")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def setup_function() -> None:
    reset_auth_state_for_tests()
    reset_notifications_state_for_tests()
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Test 1: GET default preferences — empty, well-formed
# ---------------------------------------------------------------------------


def test_get_preferences_returns_empty_for_new_parent() -> None:
    """AC3: fresh parent has no preferences → 200 with empty list."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences", headers=_parent_headers())
            assert resp.status_code == 200
            assert resp.json() == {"preferences": []}

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 2: PUT saves a single preference
# ---------------------------------------------------------------------------


def test_put_preference_saves_successfully() -> None:
    """AC1: preference is saved and returned in PUT response."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_parent_headers(), json=body
            )
            assert resp.status_code == 200
            prefs = resp.json()["preferences"]
            assert len(prefs) == 1
            assert prefs[0]["event_type"] == "grade_approved"
            assert prefs[0]["cadence"] == "daily"
            assert "updated_at" in prefs[0]
            assert prefs[0]["updated_at"]  # non-empty

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 3: GET returns updated preferences after PUT
# ---------------------------------------------------------------------------


def test_get_returns_updated_preferences_after_put() -> None:
    """AC2: GET reflects the most recently PUT preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "weekly"}]}
            await client.put("/notifications/preferences", headers=_parent_headers(), json=body)

            resp = await client.get("/notifications/preferences", headers=_parent_headers())
            assert resp.status_code == 200
            prefs = resp.json()["preferences"]
            assert any(
                p["event_type"] == "grade_approved" and p["cadence"] == "weekly" for p in prefs
            )

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 4: student role → 403
# ---------------------------------------------------------------------------


def test_student_cannot_get_notification_preferences() -> None:
    """AC5: student role is forbidden from GET /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences", headers=_student_headers())
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_student_cannot_put_notification_preferences() -> None:
    """AC5: student role is forbidden from PUT /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_student_headers(), json=body
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 5: teacher role → 403
# ---------------------------------------------------------------------------


def test_teacher_cannot_get_notification_preferences() -> None:
    """AC5: teacher role is forbidden."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences", headers=_teacher_headers())
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 5b: admin role → 403
# ---------------------------------------------------------------------------


def test_admin_cannot_get_notification_preferences() -> None:
    """AC5: admin role is forbidden from GET /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences", headers=_admin_headers())
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_admin_cannot_put_notification_preferences() -> None:
    """AC5: admin role is forbidden from PUT /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_admin_headers(), json=body
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 5c: principal role → 403
# ---------------------------------------------------------------------------


def test_principal_cannot_get_notification_preferences() -> None:
    """AC5: principal role is forbidden from GET /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences", headers=_principal_headers())
            assert resp.status_code == 403

    asyncio.run(scenario())


def test_principal_cannot_put_notification_preferences() -> None:
    """AC5: principal role is forbidden from PUT /notifications/preferences."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_principal_headers(), json=body
            )
            assert resp.status_code == 403

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 6: unauthenticated → 401
# ---------------------------------------------------------------------------


def test_unauthenticated_get_returns_401() -> None:
    """AC6: missing token → 401."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            resp = await client.get("/notifications/preferences")
            assert resp.status_code == 401

    asyncio.run(scenario())


def test_unauthenticated_put_returns_401() -> None:
    """AC6: missing token on PUT → 401."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            resp = await client.put("/notifications/preferences", json=body)
            assert resp.status_code == 401

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 7: invalid cadence → 422
# ---------------------------------------------------------------------------


def test_invalid_cadence_returns_422() -> None:
    """AC4: cadence not in {instant, daily, weekly, off} → 422."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "grade_approved", "cadence": "quarterly"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_parent_headers(), json=body
            )
            assert resp.status_code == 422

    asyncio.run(scenario())


def test_invalid_event_type_returns_422() -> None:
    """AC4 (complementary): unknown event_type also rejected with 422."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {"preferences": [{"event_type": "unknown_event", "cadence": "daily"}]}
            resp = await client.put(
                "/notifications/preferences", headers=_parent_headers(), json=body
            )
            assert resp.status_code == 422

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 8: org isolation — repo-layer
# ---------------------------------------------------------------------------


def test_preferences_are_org_scoped() -> None:
    """AC7: preferences stored under org_demo_1 are not visible under org_other_1.

    Tests repo-layer isolation directly (auth cross-check prevents cross-org token
    usage over HTTP; this validates the key structure (user_id, org_id, event_type)).
    """
    repo = InMemoryNotificationPreferencesRepository()
    repo.upsert_preference(
        user_id="usr_parent_1",
        org_id="org_demo_1",
        event_type="grade_approved",
        cadence="daily",
        updated_at="2026-03-19T10:00:00+00:00",
    )

    # Same user, different org → no results
    results = repo.get_preferences_for_user("usr_parent_1", "org_other_1")
    assert results == []

    # Original org → results present
    results_demo = repo.get_preferences_for_user("usr_parent_1", "org_demo_1")
    assert len(results_demo) == 1
    assert results_demo[0].cadence == "daily"


# ---------------------------------------------------------------------------
# Test 8b: user isolation — two parents in same org see separate preferences
# ---------------------------------------------------------------------------


def test_preferences_are_user_scoped_within_org() -> None:
    """AC7: two parents in the same org have independent preferences.

    Tests repo-layer isolation directly — the composite key (user_id, org_id, event_type)
    ensures usr_parent_1 and usr_parent_2 in the same org see separate preference sets.
    """
    repo = InMemoryNotificationPreferencesRepository()
    repo.upsert_preference(
        user_id="usr_parent_1",
        org_id="org_demo_1",
        event_type="grade_approved",
        cadence="daily",
        updated_at="2026-03-19T10:00:00+00:00",
    )

    # Different user, same org → empty
    results = repo.get_preferences_for_user("usr_parent_2", "org_demo_1")
    assert results == []

    # Original user → present
    results_p1 = repo.get_preferences_for_user("usr_parent_1", "org_demo_1")
    assert len(results_p1) == 1
    assert results_p1[0].cadence == "daily"


# ---------------------------------------------------------------------------
# Test 9: multiple event types configured independently
# ---------------------------------------------------------------------------


def test_multiple_event_types_configured_independently() -> None:
    """AC1: two event types in one PUT are each stored and returned independently."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body = {
                "preferences": [
                    {"event_type": "grade_approved", "cadence": "weekly"},
                    {"event_type": "recommendation_confirmed", "cadence": "daily"},
                ]
            }
            resp = await client.put(
                "/notifications/preferences", headers=_parent_headers(), json=body
            )
            assert resp.status_code == 200

            get_resp = await client.get("/notifications/preferences", headers=_parent_headers())
            assert get_resp.status_code == 200
            prefs = get_resp.json()["preferences"]
            assert len(prefs) == 2
            cadence_map = {p["event_type"]: p["cadence"] for p in prefs}
            assert cadence_map["grade_approved"] == "weekly"
            assert cadence_map["recommendation_confirmed"] == "daily"

    asyncio.run(scenario())


def test_upsert_updates_existing_preference() -> None:
    """AC2: subsequent PUT with same event_type updates cadence (upsert semantics)."""

    async def scenario() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            body1 = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}
            await client.put("/notifications/preferences", headers=_parent_headers(), json=body1)

            body2 = {"preferences": [{"event_type": "grade_approved", "cadence": "off"}]}
            await client.put("/notifications/preferences", headers=_parent_headers(), json=body2)

            get_resp = await client.get("/notifications/preferences", headers=_parent_headers())
            prefs = get_resp.json()["preferences"]
            # Should still have exactly one entry (upserted), with updated cadence
            grade_prefs = [p for p in prefs if p["event_type"] == "grade_approved"]
            assert len(grade_prefs) == 1
            assert grade_prefs[0]["cadence"] == "off"

    asyncio.run(scenario())


# ---------------------------------------------------------------------------
# Test 10: NFR-001 — p95 latency ≤ 700ms for GET and PUT
# ---------------------------------------------------------------------------


def test_nfr_001_get_preferences_performance() -> None:
    """NFR-001: GET /notifications/preferences p95 latency must be < 700ms.

    Runs 5 warm-up requests (discarded) then 20 measured requests in a single
    asyncio session, matching the established pattern in test_progress_api.py.
    """
    latencies: list[float] = []

    async def measure() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for _ in range(5):
                await client.get("/notifications/preferences", headers=_parent_headers())
            for _ in range(20):
                start = time.perf_counter()
                await client.get("/notifications/preferences", headers=_parent_headers())
                latencies.append((time.perf_counter() - start) * 1000)

    asyncio.run(measure())
    latencies.sort()
    p95 = latencies[int(0.95 * len(latencies))]
    assert p95 < 700, f"p95 latency {p95:.1f}ms exceeds 700ms NFR-001 threshold"


def test_nfr_001_put_preferences_performance() -> None:
    """NFR-001: PUT /notifications/preferences p95 latency must be < 700ms.

    Runs 5 warm-up requests (discarded) then 20 measured requests in a single
    asyncio session, matching the established pattern in test_progress_api.py.
    """
    latencies: list[float] = []
    body = {"preferences": [{"event_type": "grade_approved", "cadence": "daily"}]}

    async def measure() -> None:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            for _ in range(5):
                await client.put("/notifications/preferences", headers=_parent_headers(), json=body)
            for _ in range(20):
                start = time.perf_counter()
                await client.put("/notifications/preferences", headers=_parent_headers(), json=body)
                latencies.append((time.perf_counter() - start) * 1000)

    asyncio.run(measure())
    latencies.sort()
    p95 = latencies[int(0.95 * len(latencies))]
    assert p95 < 700, f"p95 latency {p95:.1f}ms exceeds 700ms NFR-001 threshold"
