import logging
import threading
import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional, Tuple
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.schemas.calendar import (
    AvailabilityResponse,
    BookingResponse,
    MeetingPassDetails,
    TimeSlot,
)

logger = logging.getLogger(__name__)


def _parse_iso(iso_str: str) -> datetime:
    """Parse ISO datetime string, supporting Python 3.9 trailing 'Z' syntax."""
    clean_str = iso_str.replace("Z", "+00:00") if iso_str.endswith("Z") else iso_str
    return datetime.fromisoformat(clean_str)


def format_dual_timezone(start_dt: datetime, end_dt: datetime, visitor_tz_str: str) -> Tuple[str, str]:
    """Format meeting window in visitor timezone and BrainCX HQ (America/New_York) timezone."""
    visitor_tz = ZoneInfo(visitor_tz_str)
    hq_tz = ZoneInfo("America/New_York")

    start_v = start_dt.astimezone(visitor_tz)
    end_v = end_dt.astimezone(visitor_tz)

    start_hq = start_dt.astimezone(hq_tz)
    end_hq = end_dt.astimezone(hq_tz)

    visitor_str = f"{start_v.strftime('%A, %b %d, %Y • %I:%M %p')} – {end_v.strftime('%I:%M %p')} ({visitor_tz_str})"
    hq_str = f"{start_hq.strftime('%A, %b %d, %Y • %I:%M %p')} – {end_hq.strftime('%I:%M %p')} (America/New_York)"
    return visitor_str, hq_str


def build_calendar_urls(title: str, description: str, meet_url: str, start_dt: datetime, end_dt: datetime) -> Tuple[str, str]:
    """Build direct web links to add to Google Calendar and Outlook."""
    import urllib.parse
    start_utc = start_dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    end_utc = end_dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")

    gcal_params = {
        "action": "TEMPLATE",
        "text": title,
        "dates": f"{start_utc}/{end_utc}",
        "details": description,
        "location": meet_url or "Google Meet Video Room",
    }
    gcal_url = f"https://calendar.google.com/calendar/render?{urllib.parse.urlencode(gcal_params)}"

    outlook_params = {
        "path": "/calendar/action/compose",
        "rru": "addevent",
        "subject": title,
        "startdt": start_utc,
        "enddt": end_utc,
        "body": description,
        "location": meet_url or "Google Meet Video Room",
    }
    outlook_url = f"https://outlook.live.com/calendar/0/deeplink/compose?{urllib.parse.urlencode(outlook_params)}"
    return gcal_url, outlook_url


def generate_ics_content(meeting_pass: MeetingPassDetails) -> str:
    """Generate an RFC 5545 compliant .ics calendar file content."""
    start_dt = _parse_iso(meeting_pass.start_iso)
    end_dt = _parse_iso(meeting_pass.end_iso)
    now_utc = datetime.now(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    start_utc = start_dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    end_utc = end_dt.astimezone(ZoneInfo("UTC")).strftime("%Y%m%dT%H%M%SZ")
    meet = meeting_pass.meet_url or "https://meet.google.com"

    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//BrainCX Inc//BrainCX Voice Representative//EN\r\n"
        "CALSCALE:GREGORIAN\r\n"
        "METHOD:REQUEST\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{meeting_pass.event_id}@braincx.com\r\n"
        f"DTSTAMP:{now_utc}\r\n"
        f"DTSTART:{start_utc}\r\n"
        f"DTEND:{end_utc}\r\n"
        f"SUMMARY:{meeting_pass.title}\r\n"
        f"DESCRIPTION:BrainCX Discovery Call with {meeting_pass.name}\\n\\nJoin Video Room: {meet}\\n\\nPowered by AI, managed by BrainCX.\\nWest Palm Beach, Florida.\r\n"
        f"LOCATION:{meet}\r\n"
        "STATUS:CONFIRMED\r\n"
        "ORGANIZER;CN=BrainCX Executive Team:mailto:team@braincx.com\r\n"
        f"ATTENDEE;CUTYPE=INDIVIDUAL;ROLE=REQ-PARTICIPANT;PARTSTAT=ACCEPTED;CN={meeting_pass.name}:mailto:{meeting_pass.email}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )


class GoogleCalendarService:
    """Service handling Google Calendar authentication, slot generation, and event booking."""

    def __init__(self):
        self._client: Optional[Any] = None
        self._mock_events: List[Dict[str, Any]] = []
        self._events_cache: Dict[str, MeetingPassDetails] = {}
        self._booking_lock = threading.Lock()



    def _get_client(self) -> Optional[Any]:
        """Authenticate and return Google Calendar API client, or None if credentials missing."""
        if self._client:
            return self._client

        if not settings.has_google_credentials:
            logger.info("Google OAuth2 credentials not set or mock values detected. Running in mock calendar mode.")
            return None

        try:
            creds = Credentials(
                token=None,
                refresh_token=settings.GOOGLE_REFRESH_TOKEN,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=["https://www.googleapis.com/auth/calendar.events"],
            )
            self._client = build("calendar", "v3", credentials=creds, cache_discovery=False)
            logger.info("Successfully initialized Google Calendar client.")
            return self._client
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar API: {str(e)}")
            return None

    def get_busy_periods(
        self,
        time_min: datetime,
        time_max: datetime,
        tz: ZoneInfo,
    ) -> List[Tuple[datetime, datetime]]:
        """Retrieve busy periods between time_min and time_max."""
        client = self._get_client()
        busy_intervals: List[Tuple[datetime, datetime]] = []

        if client:
            try:
                events_result = client.events().list(
                    calendarId=settings.GOOGLE_CALENDAR_ID,
                    timeMin=time_min.isoformat(),
                    timeMax=time_max.isoformat(),
                    singleEvents=True,
                    orderBy="startTime",
                ).execute()

                items = events_result.get("items", [])
                for item in items:
                    # Ignore cancelled events or transparent (free) events
                    if item.get("status") == "cancelled" or item.get("transparency") == "transparent":
                        continue

                    start_raw = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                    end_raw = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")

                    if not start_raw or not end_raw:
                        continue

                    try:
                        start_dt = _parse_iso(start_raw)
                        end_dt = _parse_iso(end_raw)
                        if start_dt.tzinfo is None:
                            start_dt = start_dt.replace(tzinfo=tz)
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=tz)
                        busy_intervals.append((start_dt, end_dt))
                    except Exception as parse_err:
                        logger.warning(f"Could not parse event date: {parse_err}")
            except HttpError as http_err:
                logger.error(f"Google Calendar API HTTP error: {http_err}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error fetching calendar events: {e}")
                raise
        else:
            # In mock mode, check in-memory events
            for item in self._mock_events:
                s = item["start"]
                e = item["end"]
                # Overlap test with [time_min, time_max]
                if max(s, time_min) < min(e, time_max):
                    busy_intervals.append((s, e))

        return busy_intervals

    def get_availability(self, target_date_str: str, tz_str: str) -> AvailabilityResponse:
        """
        Calculate available slots for a given date and timezone.
        Respects business hours (9:00 - 17:00) and 30-minute intervals.
        """
        tz = ZoneInfo(tz_str)
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").date()

        # Day start and day end in visitor's timezone
        day_start = datetime.combine(target_date, time.min).replace(tzinfo=tz)
        day_end = datetime.combine(target_date, time.max).replace(tzinfo=tz)

        busy_periods = self.get_busy_periods(day_start, day_end, tz)

        # Generate candidate slots within business hours
        available_slots: List[TimeSlot] = []
        now_in_tz = datetime.now(tz)

        slot_duration = timedelta(minutes=settings.MEETING_DURATION_MINUTES)
        current_slot_start = datetime.combine(
            target_date,
            time(hour=settings.BUSINESS_HOURS_START, minute=0)
        ).replace(tzinfo=tz)

        business_end = datetime.combine(
            target_date,
            time(hour=settings.BUSINESS_HOURS_END, minute=0)
        ).replace(tzinfo=tz)

        while current_slot_start + slot_duration <= business_end:
            current_slot_end = current_slot_start + slot_duration

            # 1. Check if the slot is in the past
            if current_slot_start <= now_in_tz:
                current_slot_start += slot_duration
                continue

            # 2. Check if the slot overlaps with any busy period
            is_busy = False
            for busy_start, busy_end in busy_periods:
                # Overlap condition: max(start1, start2) < min(end1, end2)
                if max(current_slot_start, busy_start) < min(current_slot_end, busy_end):
                    is_busy = True
                    break

            if not is_busy:
                # Format human-friendly display label (e.g. 10:00 AM - 10:30 AM)
                start_str_friendly = current_slot_start.strftime("%I:%M %p").lstrip("0")
                end_str_friendly = current_slot_end.strftime("%I:%M %p").lstrip("0")
                display_label = f"{start_str_friendly} - {end_str_friendly}"

                available_slots.append(
                    TimeSlot(
                        start=current_slot_start.isoformat(),
                        end=current_slot_end.isoformat(),
                        display_time=display_label,
                    )
                )

            current_slot_start += slot_duration

        return AvailabilityResponse(
            success=True,
            date=target_date_str,
            timezone=tz_str,
            available_slots=available_slots,
            count=len(available_slots),
        )

    def is_slot_available(self, start_dt: datetime, end_dt: datetime, tz: ZoneInfo) -> bool:
        """Mandatory pre-booking check to verify if the slot remains available."""
        busy_periods = self.get_busy_periods(start_dt, end_dt, tz)
        for busy_start, busy_end in busy_periods:
            if max(start_dt, busy_start) < min(end_dt, busy_end):
                return False
        return True

    def book_meeting(
        self,
        name: str,
        email: str,
        tz_str: str,
        start_iso: str,
        end_iso: str,
    ) -> BookingResponse:
        """
        Create a calendar booking after performing a mandatory pre-booking availability check.
        Never reports success unless the calendar event is actually created.
        """
        tz = ZoneInfo(tz_str)
        try:
            start_dt = _parse_iso(start_iso)
            end_dt = _parse_iso(end_iso)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=tz)
        except Exception as e:
            return BookingResponse(
                success=False,
                reason="INVALID_DATETIME",
                message=f"Could not parse start or end datetime: {str(e)}",
            )

        # Acquire lock to prevent race conditions during the check-and-insert window
        with self._booking_lock:
            # 1. Mandatory re-check: Verify slot availability immediately before event creation
            if not self.is_slot_available(start_dt, end_dt, tz):
                logger.warning(f"Booking conflict detected for slot {start_iso} to {end_iso}.")
                return BookingResponse(
                    success=False,
                    reason="TIME_UNAVAILABLE",
                    message="The requested time slot was just taken. Please choose another available time.",
                    start=start_iso,
                    end=end_iso,
                )

            client = self._get_client()

            if client:
                try:
                    event_body: Dict[str, Any] = {
                        "summary": f"BrainCX Discovery Call - {name}",
                        "description": (
                            f"BrainCX Discovery Call with {name} ({email})\n\n"
                            "Booked via BrainCX AI Voice Agent.\n"
                            "BrainCX: The AI CX Operator for high consequence verticals.\n"
                            "Powered by AI, managed by BrainCX."
                        ),
                        "start": {
                            "dateTime": start_dt.isoformat(),
                            "timeZone": tz_str,
                        },
                        "end": {
                            "dateTime": end_dt.isoformat(),
                            "timeZone": tz_str,
                        },
                        "attendees": [
                            {"email": email, "displayName": name},
                        ],
                        "reminders": {
                            "useDefault": True,
                        },
                    }

                    # Add BrainCX representative organizer attendee if configured
                    if settings.ORGANIZER_EMAIL:
                        event_body["attendees"].append({
                            "email": settings.ORGANIZER_EMAIL,
                            "displayName": "BrainCX Team",
                        })

                    # Add Google Meet video conference if enabled
                    if settings.CREATE_GOOGLE_MEET_LINK:
                        event_body["conferenceData"] = {
                            "createRequest": {
                                "requestId": f"braincx-meet-{uuid.uuid4().hex[:12]}",
                                "conferenceSolutionKey": {"type": "hangoutsMeet"},
                            }
                        }

                    created_event = client.events().insert(
                        calendarId=settings.GOOGLE_CALENDAR_ID,
                        body=event_body,
                        conferenceDataVersion=1 if settings.CREATE_GOOGLE_MEET_LINK else 0,
                        sendUpdates="all",
                    ).execute()

                    event_id = created_event.get("id")
                    if not event_id:
                        logger.error("Google Calendar did not return an event ID.")
                        return BookingResponse(
                            success=False,
                            reason="CALENDAR_ERROR",
                            message="Calendar service could not confirm event creation.",
                        )

                    # Extract Google Meet link if generated
                    meet_link = created_event.get("hangoutLink")
                    if not meet_link:
                        entry_points = created_event.get("conferenceData", {}).get("entryPoints", [])
                        if entry_points:
                            meet_link = entry_points[0].get("uri")

                    logger.info(f"Successfully created Google Calendar event: {event_id}, meet_link={meet_link}")
                    pass_details = self._create_meeting_pass(
                        event_id=event_id,
                        name=name,
                        email=email,
                        tz_str=tz_str,
                        start_dt=start_dt,
                        end_dt=end_dt,
                        meet_url=meet_link,
                    )
                    return BookingResponse(
                        success=True,
                        event_id=event_id,
                        start=start_iso,
                        end=end_iso,
                        meet_url=meet_link,
                        meeting_pass=pass_details,
                        message=f"Meeting successfully booked for {name}.",
                    )
                except HttpError as http_err:
                    logger.error(f"Google Calendar API failed during event creation: {http_err}")
                    return BookingResponse(
                        success=False,
                        reason="CALENDAR_ERROR",
                        message="Failed to create calendar event with provider.",
                    )
                except Exception as ex:
                    logger.error(f"Unexpected error creating calendar event: {ex}")
                    return BookingResponse(
                        success=False,
                        reason="CALENDAR_ERROR",
                        message="An unexpected error occurred while booking the meeting.",
                    )
            else:
                # Production validation: ensure mock mode isn't accidentally serving real users
                if settings.is_production and not settings.ENABLE_MOCK_FALLBACK:
                    logger.error("Attempted booking in production without valid Google Calendar credentials.")
                    return BookingResponse(
                        success=False,
                        reason="CALENDAR_CONFIGURATION_ERROR",
                        message="Calendar system is temporarily unavailable for scheduling.",
                    )

                # Mock mode: Record in-memory event and return simulated event ID
                mock_id = f"mock_evt_{uuid.uuid4().hex[:12]}"
                mock_meet = f"https://meet.google.com/mock-{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
                self._mock_events.append({
                    "id": mock_id,
                    "name": name,
                    "email": email,
                    "start": start_dt,
                    "end": end_dt,
                    "summary": f"BrainCX Discovery Call - {name}",
                })
                pass_details = self._create_meeting_pass(
                    event_id=mock_id,
                    name=name,
                    email=email,
                    tz_str=tz_str,
                    start_dt=start_dt,
                    end_dt=end_dt,
                    meet_url=mock_meet,
                )
                logger.info(f"Mock calendar event created: {mock_id} for {name} ({email})")
                return BookingResponse(
                    success=True,
                    event_id=mock_id,
                    start=start_iso,
                    end=end_iso,
                    meet_url=mock_meet,
                    meeting_pass=pass_details,
                    message=f"Meeting successfully booked for {name} (Mock Mode).",
                )

    def _create_meeting_pass(
        self,
        event_id: str,
        name: str,
        email: str,
        tz_str: str,
        start_dt: datetime,
        end_dt: datetime,
        meet_url: Optional[str],
    ) -> MeetingPassDetails:
        title = f"BrainCX Discovery Call - {name}"
        desc = (
            f"BrainCX Discovery Call with {name} ({email})\n\n"
            f"Google Meet Video Room: {meet_url or 'https://meet.google.com'}\n\n"
            "BrainCX: The AI CX Operator for high consequence verticals.\n"
            "Powered by AI, managed by BrainCX."
        )
        visitor_str, hq_str = format_dual_timezone(start_dt, end_dt, tz_str)
        gcal_url, _ = build_calendar_urls(title, desc, meet_url or "", start_dt, end_dt)
        ics_url = f"/api/calendar/event/{event_id}.ics"

        pass_details = MeetingPassDetails(
            event_id=event_id,
            title=title,
            name=name,
            email=email,
            start_iso=start_dt.isoformat(),
            end_iso=end_dt.isoformat(),
            visitor_timezone=tz_str,
            visitor_formatted_time=visitor_str,
            braincx_timezone="America/New_York",
            braincx_formatted_time=hq_str,
            meet_url=meet_url,
            google_calendar_url=gcal_url,
            ics_download_url=ics_url,
            status="confirmed",
            invites_dispatched=True,
            organizer="BrainCX Executive Team <team@braincx.com>",
        )
        self._events_cache[event_id] = pass_details
        return pass_details

    def get_meeting_pass(self, event_id: str) -> Optional[MeetingPassDetails]:
        """Retrieve cached or stored meeting pass for an event ID."""
        return self._events_cache.get(event_id)



    def add_mock_busy_slot(self, start_dt: datetime, end_dt: datetime):
        """Helper for unit tests to insert a busy period in mock mode."""
        self._mock_events.append({
            "id": f"mock_busy_{uuid.uuid4().hex[:8]}",
            "name": "Busy Period",
            "email": "busy@braincx.com",
            "start": start_dt,
            "end": end_dt,
            "summary": "Existing Meeting",
        })

    def clear_mock_events(self):
        """Helper for unit tests to reset mock events."""
        self._mock_events.clear()


# Singleton service instance
_calendar_service_instance = GoogleCalendarService()


def get_calendar_service() -> GoogleCalendarService:
    """Dependency provider for the calendar service."""
    return _calendar_service_instance
