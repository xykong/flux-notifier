from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get("/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_push_apns_success(client):
    with patch("app.routes.notify.send_apns", new=AsyncMock(return_value=None)):
        resp = client.post(
            "/v1/push",
            json={
                "platform": "apns",
                "device_token": "abc123",
                "title": "Hello",
                "body": "World",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    assert resp.json()["platform"] == "apns"


def test_push_fcm_success(client):
    with patch("app.routes.notify.send_fcm", new=AsyncMock(return_value=None)):
        resp = client.post(
            "/v1/push",
            json={
                "platform": "fcm",
                "device_token": "tok456",
                "title": "FCM Test",
                "body": "body text",
            },
        )
    assert resp.status_code == 200
    assert resp.json()["platform"] == "fcm"


def test_push_apns_provider_error(client):
    with patch(
        "app.routes.notify.send_apns",
        new=AsyncMock(side_effect=RuntimeError("APNs error 410")),
    ):
        resp = client.post(
            "/v1/push",
            json={"platform": "apns", "device_token": "bad", "title": "T"},
        )
    assert resp.status_code == 502
    assert "APNs error 410" in resp.json()["detail"]


def test_push_invalid_platform(client):
    resp = client.post(
        "/v1/push",
        json={"platform": "sms", "device_token": "x", "title": "T"},
    )
    assert resp.status_code == 422


def test_push_requires_api_key_when_configured(client, monkeypatch):
    monkeypatch.setattr("app.auth.settings.api_key", "secret-key")
    resp = client.post(
        "/v1/push",
        json={"platform": "apns", "device_token": "x", "title": "T"},
    )
    assert resp.status_code == 401


def test_push_accepts_valid_api_key(client, monkeypatch):
    monkeypatch.setattr("app.auth.settings.api_key", "secret-key")
    with patch("app.routes.notify.send_apns", new=AsyncMock(return_value=None)):
        resp = client.post(
            "/v1/push",
            json={"platform": "apns", "device_token": "x", "title": "T"},
            headers={"Authorization": "Bearer secret-key"},
        )
    assert resp.status_code == 200
