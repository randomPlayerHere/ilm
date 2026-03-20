"""Tests for GET /health endpoint."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_200_when_db_connected() -> None:
    mock_session = AsyncMock()
    mock_session.execute = AsyncMock()

    with patch("app.domains.health.router.async_session_factory") as mock_factory:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_ctx

        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "connected"


def test_health_returns_200_when_db_unavailable() -> None:
    with patch("app.domains.health.router.async_session_factory") as mock_factory:
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=Exception("connection refused"))
        mock_ctx.__aexit__ = AsyncMock(return_value=False)
        mock_factory.return_value = mock_ctx

        response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["db"] == "unavailable"
