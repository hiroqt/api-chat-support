from datetime import date, datetime, timedelta
from typing import Any, List, Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


TIMEZONE_MAP = {
    "pst": "America/Los_Angeles",
    "pdt": "America/Los_Angeles",
    "pt": "America/Los_Angeles",
    "pacific": "America/Los_Angeles",
    "pacific time": "America/Los_Angeles",
    "gmt-8": "America/Los_Angeles",
    "utc-8": "America/Los_Angeles",
    "gmt-7": "America/Denver",
    "utc-7": "America/Denver",
    "mst": "America/Denver",
    "mdt": "America/Denver",
    "mt": "America/Denver",
    "mountain": "America/Denver",
    "mountain time": "America/Denver",
    "cst": "America/Chicago",
    "cdt": "America/Chicago",
    "ct": "America/Chicago",
    "central": "America/Chicago",
    "central time": "America/Chicago",
    "gmt-6": "America/Chicago",
    "utc-6": "America/Chicago",
    "est": "America/New_York",
    "edt": "America/New_York",
    "et": "America/New_York",
    "eastern": "America/New_York",
    "eastern time": "America/New_York",
    "gmt-5": "America/New_York",
    "utc-5": "America/New_York",
    "gmt-4": "America/New_York",
    "utc-4": "America/New_York",
    "gmt+8": "Asia/Manila",
    "utc+8": "Asia/Manila",
    "manila": "Asia/Manila",
    "manila time": "Asia/Manila",
    "philippines": "Asia/Manila",
    "pht": "Asia/Manila",
    "singapore": "Asia/Singapore",
    "sgt": "Asia/Singapore",
    "london": "Europe/London",
    "bst": "Europe/London",
    "gmt": "UTC",
    "utc": "UTC",
    "tokyo": "Asia/Tokyo",
    "jst": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "aest": "Australia/Sydney",
}


def normalize_timezone(v: str) -> str:
    """Normalize user/voice timezone input into a valid IANA timezone identifier."""
    cleaned = v.strip()
    try:
        ZoneInfo(cleaned)
        return cleaned
    except Exception:
        pass

    key = cleaned.lower()
    if key in TIMEZONE_MAP:
        return TIMEZONE_MAP[key]

    key_simple = key.replace(" ", "").replace("-0", "-").replace("+0", "+")
    if key_simple in TIMEZONE_MAP:
        return TIMEZONE_MAP[key_simple]

    import re
    match = re.match(r"^(gmt|utc)\s*([+-])\s*(\d+)$", key)
    if match:
        sign, offset = match.group(2), int(match.group(3))
        if sign == "-" and offset == 8:
            return "America/Los_Angeles"
        elif sign == "-" and offset == 7:
            return "America/Denver"
        elif sign == "-" and offset == 6:
            return "America/Chicago"
        elif sign == "-" and offset == 5:
            return "America/New_York"
        elif sign == "+" and offset == 8:
            return "Asia/Manila"

    raise ValueError(f"Invalid IANA timezone identifier '{v}'. Examples: 'Asia/Manila', 'America/New_York'.")


def normalize_target_date(v: str) -> str:
    """
    Robust date normalizer for voice AI inputs.
    Handles:
    - Standard YYYY-MM-DD (e.g. '2026-09-18')
    - Timestamps (e.g. '2026-09-18T00:00:00')
    - LLM cutoff past-year hallucinations (e.g. '2024-09-18' -> '2026-09-18')
    - Relative voice day names ('next friday', 'this friday', 'tomorrow', 'tuesday', etc.)
    """
    cleaned = str(v).strip()
    if "T" in cleaned:
        cleaned = cleaned.split("T")[0]
    cleaned = cleaned.strip()

    current_dt = datetime.now()
    current_year = current_dt.year
    today = current_dt.date()

    lower = cleaned.lower()
    if lower in ("today",):
        return today.strftime("%Y-%m-%d")
    elif lower in ("tomorrow",):
        from datetime import timedelta
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")

    days_of_week = {
        "monday": 0, "tuesday": 1, "wednesday": 2,
        "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6
    }
    for day_name, day_idx in days_of_week.items():
        if day_name in lower:
            from datetime import timedelta
            diff = (day_idx - today.weekday()) % 7
            if diff == 0:
                diff = 7
            if "next" in lower:
                diff += 7
            return (today + timedelta(days=diff)).strftime("%Y-%m-%d")

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%B %d", "%b %d"):
        try:
            parsed_dt = datetime.strptime(cleaned, fmt)
            parsed_date = parsed_dt.date()
            if "%Y" not in fmt and "%y" not in fmt:
                parsed_date = parsed_date.replace(year=current_year)
            if parsed_date.year < current_year:
                try:
                    parsed_date = parsed_date.replace(year=current_year)
                except ValueError:
                    parsed_date = parsed_date.replace(year=current_year, day=28)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

    import re
    m = re.match(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$", cleaned)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < current_year:
            y = current_year
        return date(y, mo, d).strftime("%Y-%m-%d")

    raise ValueError(f"Invalid date format '{v}'. Expected YYYY-MM-DD (e.g. 2026-09-18).")


def normalize_iso_datetime(iso_str: str) -> str:
    """Normalize ISO datetime string, correcting any past-year cutoff hallucinations."""
    cleaned = str(iso_str).strip()
    clean_z = cleaned.replace("Z", "+00:00") if cleaned.endswith("Z") else cleaned
    dt = datetime.fromisoformat(clean_z)
    current_year = datetime.now().year
    if dt.year < current_year:
        try:
            dt = dt.replace(year=current_year)
        except ValueError:
            dt = dt.replace(year=current_year, day=28)
    return dt.isoformat()


class AvailabilityRequest(BaseModel):
    """Request schema for checking calendar availability."""
    date: str = Field(..., description="Target date in YYYY-MM-DD format", examples=["2026-09-15"])
    timezone: str = Field(default="Asia/Manila", description="IANA timezone identifier", examples=["Asia/Manila", "America/New_York"])

    @field_validator("date", mode="before")
    @classmethod
    def validate_date(cls, v: Any) -> str:
        return normalize_target_date(str(v))

    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, v: Any) -> str:
        if not v or not str(v).strip():
            return "Asia/Manila"
        return normalize_timezone(str(v))


class TimeSlot(BaseModel):
    """A discrete available meeting time slot."""
    start: str = Field(..., description="ISO 8601 start datetime with timezone offset")
    end: str = Field(..., description="ISO 8601 end datetime with timezone offset")
    display_time: str = Field(..., description="Human-friendly time label (e.g. 10:00 AM - 10:30 AM)")


class AvailabilityResponse(BaseModel):
    """Response schema containing available calendar slots."""
    success: bool = True
    date: str
    timezone: str
    available_slots: List[TimeSlot] = Field(default_factory=list)
    count: int = 0


class BookingRequest(BaseModel):
    """Request schema for booking a meeting event."""
    name: str = Field(..., min_length=2, max_length=100, description="Full name of the attendee")
    email: EmailStr = Field(..., description="Attendee email address")
    timezone: str = Field(default="Asia/Manila", description="IANA timezone identifier")
    start: str = Field(..., description="ISO 8601 start datetime")
    end: str = Field(..., description="ISO 8601 end datetime")

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 2:
            raise ValueError("Name must be at least 2 characters.")
        return cleaned

    @field_validator("timezone", mode="before")
    @classmethod
    def validate_timezone(cls, v: Any) -> str:
        if not v or not str(v).strip():
            return "Asia/Manila"
        return normalize_timezone(str(v))

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_iso_timestamps(cls, v: Any) -> str:
        return normalize_iso_datetime(str(v))

    @model_validator(mode="after")
    def validate_time_range(self) -> "BookingRequest":
        try:
            clean_start = self.start.replace("Z", "+00:00") if self.start.endswith("Z") else self.start
            start_dt = datetime.fromisoformat(clean_start)
        except Exception:
            raise ValueError("Invalid ISO datetime format for 'start'.")

        try:
            clean_end = self.end.replace("Z", "+00:00") if self.end.endswith("Z") else self.end
            end_dt = datetime.fromisoformat(clean_end)
        except Exception:
            raise ValueError("Invalid ISO datetime format for 'end'.")

        if end_dt <= start_dt:
            raise ValueError("'end' datetime must be strictly after 'start' datetime.")

        return self


class BookingResponse(BaseModel):
    """Response schema for meeting booking."""
    success: bool
    event_id: Optional[str] = None
    reason: Optional[str] = None
    message: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
