from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient

from app.services.google_calendar import format_dual_timezone, get_calendar_service


def test_dual_timezone_formatting_accuracy():
    """Verify that dual timezone formatting converts time accurately to visitor timezone and BrainCX HQ (America/New_York)."""
    # 2:00 PM Manila is 2:00 AM New York (EDT, UTC-4) on Sept 15, 2026
    start_dt = datetime(2026, 9, 15, 14, 0, tzinfo=ZoneInfo("Asia/Manila"))
    end_dt = datetime(2026, 9, 15, 14, 30, tzinfo=ZoneInfo("Asia/Manila"))

    visitor_str, hq_str = format_dual_timezone(start_dt, end_dt, "Asia/Manila")

    assert "Tuesday, Sep 15, 2026 • 02:00 PM – 02:30 PM (Asia/Manila)" in visitor_str
    assert "Tuesday, Sep 15, 2026 • 02:00 AM – 02:30 AM (America/New_York)" in hq_str


def test_booking_response_includes_meeting_pass(client: TestClient):
    """Booking an available slot must return a populated meeting_pass object."""
    future_date = (datetime.now() + timedelta(days=9)).strftime("%Y-%m-%d")
    payload = {
        "name": "Sarah Connor",
        "email": "sarah@cyberdyne.com",
        "timezone": "America/Los_Angeles",
        "start": f"{future_date}T10:00:00-07:00",
        "end": f"{future_date}T10:30:00-07:00",
    }
    response = client.post("/api/calendar/book", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["event_id"] is not None

    # Verify meeting_pass structure
    pass_data = data.get("meeting_pass")
    assert pass_data is not None
    assert pass_data["event_id"] == data["event_id"]
    assert pass_data["name"] == "Sarah Connor"
    assert pass_data["email"] == "sarah@cyberdyne.com"
    assert pass_data["visitor_timezone"] == "America/Los_Angeles"
    assert "America/Los_Angeles" in pass_data["visitor_formatted_time"]
    assert "America/New_York" in pass_data["braincx_formatted_time"]
    assert pass_data["meet_url"] is not None
    assert "meet.google.com" in pass_data["meet_url"]
    assert pass_data["google_calendar_url"] is not None
    assert f"/api/calendar/event/{data['event_id']}.ics" == pass_data["ics_download_url"]
    assert pass_data["invites_dispatched"] is True


def test_ics_calendar_download_endpoint(client: TestClient):
    """Verify that GET /api/calendar/event/{event_id}.ics returns a valid RFC 5545 iCalendar stream."""
    future_date = (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
    payload = {
        "name": "Marcus Wright",
        "email": "marcus@resistance.org",
        "timezone": "Asia/Manila",
        "start": f"{future_date}T11:00:00+08:00",
        "end": f"{future_date}T11:30:00+08:00",
    }
    book_res = client.post("/api/calendar/book", json=payload)
    event_id = book_res.json()["event_id"]

    # Request the .ics download
    ics_res = client.get(f"/api/calendar/event/{event_id}.ics")
    assert ics_res.status_code == 200
    assert "text/calendar" in ics_res.headers["content-type"]
    assert f'filename="braincx-meeting-{event_id}.ics"' in ics_res.headers.get("content-disposition", "")

    ics_content = ics_res.text
    assert "BEGIN:VCALENDAR" in ics_content
    assert "VERSION:2.0" in ics_content
    assert f"UID:{event_id}@braincx.com" in ics_content
    assert "SUMMARY:BrainCX Discovery Call - Marcus Wright" in ics_content
    assert "ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;CN=Marcus Wright:mailto:marcus@resistance.org" in ics_content
    assert "END:VCALENDAR" in ics_content


def test_ics_download_not_found(client: TestClient):
    """Requesting an .ics file for a non-existent event ID returns 404."""
    response = client.get("/api/calendar/event/non_existent_evt_999.ics")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_meeting_pass_endpoint(client: TestClient):
    """GET /api/calendar/event/{event_id} returns structured pass data."""
    future_date = (datetime.now() + timedelta(days=11)).strftime("%Y-%m-%d")
    payload = {
        "name": "Kyle Reese",
        "email": "kyle@future.org",
        "timezone": "America/Chicago",
        "start": f"{future_date}T13:00:00-05:00",
        "end": f"{future_date}T13:30:00-05:00",
    }
    book_res = client.post("/api/calendar/book", json=payload)
    event_id = book_res.json()["event_id"]

    pass_res = client.get(f"/api/calendar/event/{event_id}")
    assert pass_res.status_code == 200
    data = pass_res.json()
    assert data["event_id"] == event_id
    assert data["name"] == "Kyle Reese"
    assert data["email"] == "kyle@future.org"


def test_resend_confirmation_endpoint(client: TestClient):
    """POST /api/calendar/resend-confirmation confirms re-dispatch to attendee."""
    future_date = (datetime.now() + timedelta(days=12)).strftime("%Y-%m-%d")
    payload = {
        "name": "John Connor",
        "email": "leader@resistance.org",
        "timezone": "Asia/Manila",
        "start": f"{future_date}T16:00:00+08:00",
        "end": f"{future_date}T16:30:00+08:00",
    }
    book_res = client.post("/api/calendar/book", json=payload)
    event_id = book_res.json()["event_id"]

    resend_payload = {
        "event_id": event_id,
        "email": "leader@resistance.org",
    }
    res = client.post("/api/calendar/resend-confirmation", json=resend_payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["success"] is True
    assert res_data["event_id"] == event_id
    assert res_data["email"] == "leader@resistance.org"
    assert "successfully resent" in res_data["message"].lower()


def test_vapi_booking_tool_call_includes_meeting_pass(client: TestClient):
    """Vapi webhook tool call returns meeting_pass inside tool result."""
    future_date = (datetime.now() + timedelta(days=13)).strftime("%Y-%m-%d")
    vapi_payload = {
        "message": {
            "type": "tool-calls",
            "toolCalls": [
                {
                    "id": "call_vapi_pass_test",
                    "type": "function",
                    "function": {
                        "name": "book_meeting",
                        "arguments": {
                            "name": "Dr. Silberman",
                            "email": "silberman@clinic.org",
                            "timezone": "America/New_York",
                            "start": f"{future_date}T15:00:00-04:00",
                            "end": f"{future_date}T15:30:00-04:00"
                        }
                    }
                }
            ]
        }
    }
    response = client.post("/api/calendar/book", json=vapi_payload)
    assert response.status_code == 200
    data = response.json()
    res = data["results"][0]
    assert res["result"]["success"] is True
    assert "meeting_pass" in res["result"]
    assert res["result"]["meeting_pass"] is not None
    assert res["result"]["meeting_pass"]["name"] == "Dr. Silberman"
    assert res["result"]["meeting_pass"]["meet_url"] is not None
