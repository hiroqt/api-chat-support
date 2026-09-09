# BrainCX AI Voice Agent — Architecture & Technical Design Document (ARD)

**Version:** 1.0  
**Status:** Authoritative  
**Stack:** Next.js (TypeScript) → Vapi → FastAPI (Python) → Google Calendar API  

---

## 1. Architectural Philosophy

The core architectural principle of this system is:
> **"Let AI handle the conversation. Let code handle the rules. Let Google Calendar handle the truth."**

- **Vapi**: Intent detection, natural conversation, email/slot confirmation, and tool calling.
- **FastAPI**: Input validation, business logic, timezone conversions, conflict checks, and error masking.
- **Google Calendar API**: The single source of truth for availability and scheduled events.

There is strictly:
- No database
- No n8n or low-code automation
- No Redis/caching layer for availability
- No multi-agent autonomous framework
- No phone-number telephony integration

---

## 2. System Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                      Client Browser                         │
│   Next.js (React 19 / TypeScript) + @vapi-ai/web SDK        │
└──────────────┬───────────────────────────────▲──────────────┘
               │ Audio Stream                  │ Audio Stream
               ▼                               │
┌──────────────────────────────────────────────┴──────────────┐
│                      Vapi Voice Cloud                       │
│   - Speech-to-Text (Deepgram Nova-2)                        │
│   - LLM Orchestration (Approved BrainCX Knowledge)          │
│   - Text-to-Speech (Natural Low-Latency Voice)              │
│   - Tools: check_availability, book_meeting                 │
└──────────────┬──────────────────────────────────────────────┘
               │ HTTP POST (Tool Call Payload)
               ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
│   - Validation (Pydantic, EmailStr, ZoneInfo)               │
│   - Calendar Service (Deterministic Slot Calculation)       │
│   - Mandatory Pre-Booking Re-Check                          │
│   - Structured Error Handling (TIME_UNAVAILABLE)            │
└──────────────┬───────────────────────────────▲──────────────┘
               │ OAuth2 API Call               │ Event / FreeBusy
               ▼                               │
┌──────────────────────────────────────────────┴──────────────┐
│                    Google Calendar API                      │
│   - Authoritative Busy Periods                              │
│   - Event Creation & ID Confirmation                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 Next.js Frontend
- **Responsibilities:**
  - Initialize Vapi client with client-safe credentials (`NEXT_PUBLIC_VAPI_PUBLIC_KEY`).
  - Render interactive call controls (Start, Mute, End).
  - Provide live feedback for conversation states: `Ready`, `Connecting`, `Listening`, `Speaking`, `Booking`, `Booked`, `Error`.
  - Maintain an interactive live transcript drawer.
  - Apply clean, authoritative corporate styling avoiding excessive AI-slop gradients.

### 3.2 FastAPI Backend
- **Endpoints:**
  1. `GET /health` → `{"status": "ok"}`
  2. `POST /api/calendar/availability` → Body: `{"date": "YYYY-MM-DD", "timezone": "Asia/Manila"}`
  3. `POST /api/calendar/book` → Body: `{"name": "...", "email": "...", "timezone": "...", "start": "...", "end": "..."}`
- **Security:**
  - Secrets loaded via environment variables (`pydantic-settings`).
  - Never leaks credentials in responses, tools, or logs.
  - Masked errors: technical stack traces are never exposed; returns structured reasons (e.g. `TIME_UNAVAILABLE`, `CALENDAR_ERROR`).

### 3.3 Google Calendar Service
- **Authentication:** OAuth2 User Refresh Token using `google.oauth2.credentials.Credentials`.
- **Slot Calculation:**
  - Business hours: 09:00 to 17:00 in the visitor's requested timezone.
  - Duration: 30 minutes.
  - Buffer / Step: 30 minutes.
  - Filter: Excludes any slot overlapping with existing events or in the past.
- **Booking Sequence:**
  - Validates request payload.
  - **Mandatory final re-check:** Queries Google Calendar for any conflict within `[start, end]`.
  - If conflict exists: returns `{"success": false, "reason": "TIME_UNAVAILABLE"}`.
  - If free: calls `events().insert()`, verifies returned `event_id`, and returns `{"success": true, "event_id": event_id}`.

---

## 4. Vapi Tool Specifications

### `check_availability`
- **Description:** Retrieve real available meeting times from the Google Calendar backend.
- **Parameters:**
  - `date` (string): Date in `YYYY-MM-DD` format.
  - `timezone` (string): Valid IANA timezone identifier (e.g. `Asia/Manila`, `America/New_York`).
- **Endpoint:** `POST /api/calendar/availability`

### `book_meeting`
- **Description:** Book an actual calendar event after the visitor confirms their details.
- **Parameters:**
  - `name` (string): Full name of visitor.
  - `email` (string): Validated and confirmed email address.
  - `timezone` (string): IANA timezone identifier.
  - `start` (string): ISO 8601 start timestamp.
  - `end` (string): ISO 8601 end timestamp.
- **Endpoint:** `POST /api/calendar/book`

---

## 5. Directory Structure

```text
/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   └── routes/
│   │   │       └── calendar.py
│   │   ├── schemas/
│   │   │   └── calendar.py
│   │   ├── services/
│   │   │   └── google_calendar.py
│   │   └── core/
│   │       └── config.py
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_calendar.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   └── globals.css
│   ├── components/
│   │   ├── VoiceWidget.tsx
│   │   ├── TranscriptPanel.tsx
│   │   └── BrandHeader.tsx
│   ├── lib/
│   │   └── vapi.ts
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example
├── prompts/
│   └── system-prompt.txt
├── vapi-assistant-config.json
├── PRD.md
├── ARD.md
├── AGENTS.md
└── README.md
```
