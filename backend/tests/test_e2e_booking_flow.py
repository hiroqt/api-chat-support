import pytest
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from app.main import app
from app.services.google_calendar import get_calendar_service


@pytest.fixture
def client():
    """Create a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_calendar():
    """Ensure calendar state is isolated for each test."""
    service = get_calendar_service()
    service.clear_mock_events()
    yield
    service.clear_mock_events()


def test_e2e_full_discovery_to_booking_lifecycle(client: TestClient):
    """
    E2E Test: Simulates the entire voice agent conversation flow:
    1. Verify service health.
    2. Visitor inquires about availability for next week (Asia/Manila).
    3. Backend returns available business-hour slots.
    4. Visitor corrects their date from Tuesday to Thursday.
    5. Backend returns slots for the updated date.
    6. Visitor selects a slot and provides initial email with spelling mistake.
    7. Visitor corrects email.
    8. Agent confirms details and books meeting.
    9. Backend performs pre-booking check, creates event, and returns event ID.
    10. Subsequent check verifies that specific slot is now occupied.
    """
    # Step 1: Health check
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok"}

    # Step 2: Query availability for initial date (Tuesday)
    tuesday_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
    tz_str = "Asia/Manila"

    avail_req_1 = {
        "date": tuesday_date,
        "timezone": tz_str,
    }
    avail_resp_1 = client.post("/api/calendar/availability", json=avail_req_1)
    assert avail_resp_1.status_code == 200
    data_1 = avail_resp_1.json()
    assert data_1["success"] is True
    assert len(data_1["available_slots"]) > 0

    # Step 3: Visitor changes mind ("Actually, Thursday is better")
    thursday_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    avail_req_2 = {
        "date": thursday_date,
        "timezone": tz_str,
    }
    avail_resp_2 = client.post("/api/calendar/availability", json=avail_req_2)
    assert avail_resp_2.status_code == 200
    data_2 = avail_resp_2.json()
    assert data_2["success"] is True
    assert len(data_2["available_slots"]) > 0

    # Step 4: Visitor selects the 10:00 AM slot
    selected_slot = None
    for slot in data_2["available_slots"]:
        if "10:00 AM" in slot["display_time"]:
            selected_slot = slot
            break

    if not selected_slot:
        selected_slot = data_2["available_slots"][0]

    # Step 5: Email validation rejection if visitor spoke invalid email
    bad_booking_payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor-at-sky-dot-net",  # Invalid email format from voice STT
        "timezone": tz_str,
        "start": selected_slot["start"],
        "end": selected_slot["end"],
    }
    bad_book_resp = client.post("/api/calendar/book", json=bad_booking_payload)
    assert bad_book_resp.status_code == 422
    assert bad_book_resp.json()["success"] is False

    # Step 6: Visitor corrects email and confirms details
    corrected_booking_payload = {
        "name": "Sarah Connor",
        "email": "sarah.connor@cyberdyne.com",
        "timezone": tz_str,
        "start": selected_slot["start"],
        "end": selected_slot["end"],
    }
    book_resp = client.post("/api/calendar/book", json=corrected_booking_payload)
    assert book_resp.status_code == 200
    book_data = book_resp.json()
    assert book_data["success"] is True
    assert book_data["event_id"] is not None
    assert "Sarah Connor" in book_data["message"]

    # Step 7: Re-check availability for Thursday - the booked slot must no longer appear
    recheck_resp = client.post("/api/calendar/availability", json=avail_req_2)
    recheck_data = recheck_resp.json()
    remaining_starts = [s["start"] for s in recheck_data["available_slots"]]
    assert selected_slot["start"] not in remaining_starts


def test_e2e_booking_contention_race_condition(client: TestClient):
    """
    E2E Test: Simulates race condition where two visitors try to claim
    the exact same slot simultaneously.
    - Visitor A's booking completes.
    - Visitor B's booking is rejected with TIME_UNAVAILABLE.
    """
    future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    tz = "America/New_York"

    # Query slots
    avail_resp = client.post(
        "/api/calendar/availability",
        json={"date": future_date, "timezone": tz},
    )
    assert avail_resp.status_code == 200
    slots = avail_resp.json()["available_slots"]
    target_slot = slots[0]

    # Caller 1 books
    payload_1 = {
        "name": "User One",
        "email": "user1@enterprise.org",
        "timezone": tz,
        "start": target_slot["start"],
        "end": target_slot["end"],
    }
    resp1 = client.post("/api/calendar/book", json=payload_1)
    assert resp1.status_code == 200
    assert resp1.json()["success"] is True

    # Caller 2 tries to book the same slot
    payload_2 = {
        "name": "User Two",
        "email": "user2@enterprise.org",
        "timezone": tz,
        "start": target_slot["start"],
        "end": target_slot["end"],
    }
    resp2 = client.post("/api/calendar/book", json=payload_2)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["success"] is False
    assert data2["reason"] == "TIME_UNAVAILABLE"


def test_e2e_multi_timezone_conversion(client: TestClient):
    """
    E2E Test: Tests availability queries across different global timezones
    (e.g., Asia/Manila vs America/New_York vs Europe/London) to ensure
    time offsets and business hours are computed correctly.
    """
    target_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")

    for tz in ["Asia/Manila", "America/New_York", "Europe/London", "America/Los_Angeles"]:
        resp = client.post(
            "/api/calendar/availability",
            json={"date": target_date, "timezone": tz},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["timezone"] == tz
        assert len(data["available_slots"]) > 0

        # Verify all slot ISO strings contain valid offsets
        for slot in data["available_slots"]:
            start_dt = datetime.fromisoformat(slot["start"])
            assert start_dt.tzinfo is not None
