from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.services.google_calendar import get_calendar_service


def test_health_endpoint(client: TestClient):
    """Health check endpoint must return 200 and status: ok without depending on Calendar."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_availability_valid(client: TestClient):
    """Availability with valid date and timezone returns available slots."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    payload = {
        "date": future_date,
        "timezone": "Asia/Manila",
    }
    response = client.post("/api/calendar/availability", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["date"] == future_date
    assert data["timezone"] == "Asia/Manila"
    assert "available_slots" in data
    assert isinstance(data["available_slots"], list)
    assert len(data["available_slots"]) > 0

    first_slot = data["available_slots"][0]
    assert "start" in first_slot
    assert "end" in first_slot
    assert "display_time" in first_slot


def test_availability_invalid_date(client: TestClient):
    """Availability request with invalid date format must return 422 validation error."""
    payload = {
        "date": "invalid-date",
        "timezone": "America/New_York",
    }
    response = client.post("/api/calendar/availability", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "VALIDATION_ERROR"


def test_availability_invalid_timezone(client: TestClient):
    """Availability request with invalid IANA timezone must return 422."""
    payload = {
        "date": "2026-10-15",
        "timezone": "Invalid/Timezone",
    }
    response = client.post("/api/calendar/availability", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "VALIDATION_ERROR"


def test_booking_invalid_email(client: TestClient):
    """Booking with invalid email must return 422 validation error."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    payload = {
        "name": "Jane Doe",
        "email": "not-an-email",
        "timezone": "America/New_York",
        "start": f"{future_date}T10:00:00-04:00",
        "end": f"{future_date}T10:30:00-04:00",
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "VALIDATION_ERROR"


def test_booking_invalid_time_range(client: TestClient):
    """Booking with end time before start time must return 422 validation error."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "timezone": "America/New_York",
        "start": f"{future_date}T11:00:00-04:00",
        "end": f"{future_date}T10:00:00-04:00",  # End before start
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "VALIDATION_ERROR"


def test_booking_success(client: TestClient):
    """Booking an available slot returns success and an event_id."""
    future_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    tz_str = "America/New_York"
    start_iso = f"{future_date}T10:00:00-04:00"
    end_iso = f"{future_date}T10:30:00-04:00"

    payload = {
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "timezone": tz_str,
        "start": start_iso,
        "end": end_iso,
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["event_id"] is not None
    assert "Alex Johnson" in data["message"]


def test_booking_conflict_handling(client: TestClient):
    """
    If a slot is already occupied, booking must return success: false
    with reason: TIME_UNAVAILABLE.
    """
    service = get_calendar_service()
    future_date_obj = (datetime.now() + timedelta(days=6)).date()
    tz = ZoneInfo("Asia/Manila")

    # Add a busy slot
    busy_start = datetime.combine(future_date_obj, time(14, 0)).replace(tzinfo=tz)
    busy_end = datetime.combine(future_date_obj, time(14, 30)).replace(tzinfo=tz)
    service.add_mock_busy_slot(busy_start, busy_end)

    # Attempt to book the same slot
    payload = {
        "name": "Conflict Tester",
        "email": "tester@example.com",
        "timezone": "Asia/Manila",
        "start": busy_start.isoformat(),
        "end": busy_end.isoformat(),
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["reason"] == "TIME_UNAVAILABLE"


def test_double_booking_prevention(client: TestClient):
    """
    Two consecutive booking calls for the same slot:
    First must succeed, second must fail with TIME_UNAVAILABLE.
    """
    future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    start_iso = f"{future_date}T15:00:00+08:00"
    end_iso = f"{future_date}T15:30:00+08:00"

    payload1 = {
        "name": "First Caller",
        "email": "caller1@example.com",
        "timezone": "Asia/Manila",
        "start": start_iso,
        "end": end_iso,
    }
    resp1 = client.post("/api/calendar/book", json=payload1)
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    # Immediate second booking for the identical slot
    payload2 = {
        "name": "Second Caller",
        "email": "caller2@example.com",
        "timezone": "Asia/Manila",
        "start": start_iso,
        "end": end_iso,
    }
    resp2 = client.post("/api/calendar/book", json=payload2)
    assert resp2.status_code == 200
    assert resp2.json()["success"] is False
    assert resp2.json()["reason"] == "TIME_UNAVAILABLE"


def test_calendar_service_error_handling(client: TestClient):
    """If calendar service raises an exception during booking, returns CALENDAR_ERROR without stack trace."""
    future_date = (datetime.now() + timedelta(days=8)).strftime("%Y-%m-%d")
    payload = {
        "name": "Error Tester",
        "email": "error@example.com",
        "timezone": "America/New_York",
        "start": f"{future_date}T11:00:00-04:00",
        "end": f"{future_date}T11:30:00-04:00",
    }

    with patch.object(get_calendar_service(), "book_meeting", side_effect=Exception("Database network timeout")):
        response = client.post("/api/calendar/book", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["reason"] == "CALENDAR_ERROR"
        # Confirm internal trace is not in message
        assert "Database network timeout" not in data.get("message", "")


def test_vapi_availability_tool_call_format(client: TestClient):
    """Verify that Vapi webhook formatted tool-calls are handled and return {results: [...]}."""
    future_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_test_123",
                    "type": "function",
                    "function": {
                        "name": "check_availability",
                        "arguments": {
                            "date": future_date,
                            "timezone": "Asia/Manila"
                        }
                    }
                }
            ]
        }
    }
    response = client.post("/api/calendar/availability", json=vapi_payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert len(data["results"]) == 1
    res = data["results"][0]
    assert res["toolCallId"] == "call_vapi_test_123"
    assert res["result"]["success"] is True
    assert res["result"]["count"] > 0


def test_vapi_booking_tool_call_format(client: TestClient):
    """Verify that Vapi booking tool-calls succeed and return formatted result with toolCallId."""
    future_date = (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d")
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_book_456",
                    "type": "function",
                    "function": {
                        "name": "book_meeting",
                        "arguments": {
                            "name": "Vapi Caller",
                            "email": "caller@vapi.ai",
                            "timezone": "Asia/Manila",
                            "start": f"{future_date}T14:00:00+08:00",
                            "end": f"{future_date}T14:30:00+08:00"
                        }
                    }
                }
            ]
        }
    }
    response = client.post("/api/calendar/book", json=vapi_payload)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    res = data["results"][0]
    assert res["toolCallId"] == "call_book_456"
    assert res["result"]["success"] is True
    assert res["result"]["event_id"] is not None


def test_date_normalization_past_year_resilience(client: TestClient):
    """Verify that an LLM sending a past year (cutoff hallucination) is rolled forward to current year."""
    from app.schemas.calendar import AvailabilityRequest, normalize_target_date
    current_year = str(datetime.now().year)

    # 2024-09-18 should roll forward to 2026-09-18
    normalized = normalize_target_date("2024-09-18")
    assert normalized == f"{current_year}-09-18"

    # AvailabilityRequest should succeed with past year and normalize it
    req = AvailabilityRequest.model_validate({"date": "2024-09-18"})
    assert req.date == f"{current_year}-09-18"
    assert req.timezone == "Asia/Manila"


def test_date_normalization_relative_days(client: TestClient):
    """Verify that relative voice days like 'next friday' or 'tomorrow' are resolved."""
    from app.schemas.calendar import normalize_target_date

    next_friday = normalize_target_date("next friday")
    assert next_friday.startswith("2026-")

    tomorrow = normalize_target_date("tomorrow")
    expected_tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert tomorrow == expected_tomorrow


def test_voice_email_transcription_whitespace_cleaning(client: TestClient):
    """Verify that transcription artifacts like 'hr. is172025@gmail.com' are cleaned to 'hr.is172025@gmail.com'."""
    from app.schemas.calendar import BookingRequest
    req = BookingRequest.model_validate({
        "name": "Arnel",
        "email": "hr. is172025@gmail.com",
        "timezone": "Asia/Manila",
        "start": "2026-09-11T10:00:00+08:00",
        "end": "2026-09-11T10:30:00+08:00",
    })
    assert req.email == "hr.is172025@gmail.com"


def test_timezone_offset_reconciliation_pdt_to_manila(client: TestClient):
    """
    Verify that if the voice LLM sends a timestamp with its default server offset (-07:00 PDT)
    for an Asia/Manila meeting (e.g. 10:00 AM or 17:30), the backend reconciles the offset
    to +08:00 rather than shifting the user's intended hour by 15 hours.
    """
    from app.schemas.calendar import BookingRequest
    # 10:00 AM requested with -07:00 attached by foreign server
    req_10am = BookingRequest.model_validate({
        "name": "Arnel",
        "email": "hr. is172025@gmail.com",
        "timezone": "Asia/Manila",
        "start": "2026-09-11T10:00:00-07:00",
        "end": "2026-09-11T10:30:00-07:00",
    })
    assert req_10am.start == "2026-09-11T10:00:00+08:00"
    assert req_10am.end == "2026-09-11T10:30:00+08:00"

    # 5:30 PM requested with -07:00 attached by foreign server
    req_530pm = BookingRequest.model_validate({
        "name": "Arnel",
        "email": "arnel@example.com",
        "timezone": "Asia/Manila",
        "start": "2026-09-11T17:30:00-07:00",
        "end": "2026-09-11T18:00:00-07:00",
    })
    assert req_530pm.start == "2026-09-11T17:30:00+08:00"
    assert req_530pm.end == "2026-09-11T18:00:00+08:00"


def test_booking_with_voice_transcript_payload(client: TestClient):
    """Verify direct end-to-end booking of the exact user transcript flow."""
    payload = {
        "name": "Arnel",
        "email": "hr. is172025@gmail.com",
        "timezone": "Asia/Manila",
        "start": "2026-09-11T10:00:00-07:00",
        "end": "2026-09-11T10:30:00-07:00",
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["start"] == "2026-09-11T10:00:00+08:00"
    assert data["meeting_pass"]["visitor_formatted_time"].startswith("Friday, Sep 11, 2026 • 10:00 AM")

