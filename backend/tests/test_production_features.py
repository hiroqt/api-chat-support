from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings


def test_liveness_and_readiness_probes(client: TestClient):
    """Test container liveness (/health/live) and readiness (/health/ready) endpoints."""
    live_resp = client.get("/health/live")
    assert live_resp.status_code == 200
    assert live_resp.json()["status"] == "ok"
    assert "environment" in live_resp.json()

    ready_resp = client.get("/health/ready")
    assert ready_resp.status_code == 200
    assert ready_resp.json()["status"] == "ready"


def test_vapi_auth_enforcement_and_headers(client: TestClient):
    """When VAPI_SECRET_TOKEN is set, unauthorized requests must be rejected with 401."""
    original_secret = settings.VAPI_SECRET_TOKEN
    settings.VAPI_SECRET_TOKEN = "super-secret-prod-token-12345"

    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    payload = {"date": future_date, "timezone": "Asia/Manila"}

    try:
        # 1. Without auth header -> 401
        unauth_resp = client.post("/api/calendar/availability", json=payload)
        assert unauth_resp.status_code == 401
        assert "Unauthorized" in unauth_resp.json().get("detail", "")

        # 2. With wrong auth header -> 401
        wrong_resp = client.post(
            "/api/calendar/availability",
            json=payload,
            headers={"X-Vapi-Secret": "wrong-token"},
        )
        assert wrong_resp.status_code == 401

        # 3. With valid X-Vapi-Secret header -> 200
        valid_resp1 = client.post(
            "/api/calendar/availability",
            json=payload,
            headers={"X-Vapi-Secret": "super-secret-prod-token-12345"},
        )
        assert valid_resp1.status_code == 200
        assert valid_resp1.json()["success"] is True

        # 4. With valid Bearer Authorization header -> 200
        valid_resp2 = client.post(
            "/api/calendar/availability",
            json=payload,
            headers={"Authorization": "Bearer super-secret-prod-token-12345"},
        )
        assert valid_resp2.status_code == 200
        assert valid_resp2.json()["success"] is True
    finally:
        settings.VAPI_SECRET_TOKEN = original_secret


def test_booking_includes_google_meet_link(client: TestClient):
    """Booking response should include a generated Google Meet video URL."""
    future_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
    start_iso = f"{future_date}T10:00:00+08:00"
    end_iso = f"{future_date}T10:30:00+08:00"

    payload = {
        "name": "Production Attendee",
        "email": "prod.attendee@braincx.com",
        "timezone": "Asia/Manila",
        "start": start_iso,
        "end": end_iso,
    }

    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["event_id"] is not None
    assert "meet_url" in data
    assert data["meet_url"] is not None
    assert "meet.google.com" in data["meet_url"]


def test_vapi_call_summary_webhook(client: TestClient):
    """Test receiving Vapi end-of-call summary webhook."""
    payload = {
        "durationSeconds": 142.5,
        "summary": "Visitor inquired about higher education 200% lift metric and booked a Tuesday discovery meeting.",
        "recordingUrl": "https://api.vapi.ai/recordings/rec_123456.mp3",
    }
    response = client.post("/api/calendar/call-summary", json=payload)
    assert response.status_code == 200
    assert response.json() == {"status": "received"}


def test_security_headers_present(client: TestClient):
    """Test that production security headers are attached to responses."""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Response-Time" in resp.headers
