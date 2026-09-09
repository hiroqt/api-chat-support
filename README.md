# BrainCX AI Voice Agent

Production-quality, assessment-ready web-based voice agent for BrainCX that represents the company accurately, understands visitor needs, and reliably checks and schedules meetings via live Google Calendar integration.

Built according to the authoritative project specifications in `PRD.md`, `ARD.md`, and `AGENTS.md`.

---

## 1. Core Architecture

The architecture enforces a strict separation of concerns:
> **"Let AI handle the conversation. Let code handle the rules. Let Google Calendar handle the truth."**

```text
Browser (Next.js)
       ↓  (WebRTC audio stream)
Vapi Voice Cloud (STT + LLM + TTS)
       ↓  (HTTP POST tool calls)
FastAPI Backend (Validation + Timezones + Deterministic Slot Engine)
       ↓  (OAuth 2.0 API calls)
Google Calendar API (Authoritative Truth)
```

### What is Explicitly NOT Used
- No n8n or low-code workflow builders
- No database or Redis caching
- No CRM integration
- No phone numbers / telephony SIP trunks
- No multi-agent autonomous swarms

---

## 2. Key Features

- **Accurate BrainCX Knowledge**: Strictly adheres to authorized company information (West Palm Beach, FL; founded 2021 by Tariq Alinur & Rose Flores; Tariq's background at Apple, JPMorgan Chase, American Express; higher education, healthcare, and telecom metrics; outcome-based pricing; SOC 2 Type II & HIPAA compliance).
- **Prohibited Claims Enforced**: Strictly rejects headcount-reduction language: *"The platform gives existing agents more capacity. It does not replace them."*
- **Natural Voice Experience**: Sub-300ms latency, turn-taking, fluid interruption handling, silence tolerance, and friction-free email/date corrections.
- **Deterministic Google Calendar Availability**: Generates valid 30-minute meeting slots during business hours (9:00 AM – 5:00 PM) in any requested IANA timezone (e.g., `Asia/Manila`, `America/New_York`).
- **Mandatory Pre-Booking Re-Check**: Before inserting any calendar event, the backend re-verifies that the selected slot remains unbooked, preventing race conditions or double-bookings.
- **Refined Enterprise Design**: Clean dark aesthetic avoiding flashy AI slop, rainbow gradients, and gimmicky eyebrow pills.

---

## 3. Project Structure

```text
braincx-voice-agent/
│
├── frontend/                        # Next.js 14 Web Application
│   ├── app/                         # App router (layout.tsx, page.tsx, globals.css)
│   ├── components/                  # BrandHeader, VoiceWidget, TranscriptPanel
│   ├── lib/                         # Vapi client initialization helper
│   ├── package.json
│   ├── tsconfig.json
│   └── .env.example                 # Frontend mock configuration
│
├── backend/                         # FastAPI Python Service
│   ├── app/
│   │   ├── api/routes/calendar.py   # /api/calendar/availability & /api/calendar/book
│   │   ├── schemas/calendar.py      # Pydantic schemas (EmailStr, IANA timezone)
│   │   ├── services/google_calendar.py # Google Calendar API service & slot engine
│   │   ├── core/config.py           # Pydantic settings
│   │   └── main.py                  # FastAPI app, CORS, /health
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_calendar.py         # Pytest test suite (10 test cases)
│   ├── requirements.txt
│   └── .env.example                 # Backend mock configuration
│
├── prompts/
│   └── system-prompt.txt            # System prompt for Vapi Assistant
│
├── vapi-assistant-config.json       # 1-Click Vapi Assistant JSON configuration
├── PRD.md                           # Product Requirements Document
├── ARD.md                           # Architecture & Technical Design Document
├── AGENTS.md                        # Coding agent guidelines & constraints
└── README.md
```

---

## 4. Quickstart Guide

### Prerequisites
- Python 3.9+ (or uv)
- Node.js 18+ and npm

---

### Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create a virtual environment and install dependencies**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   *(Note: When Google Calendar credentials are not configured or set to mock values, the backend runs in a deterministic in-memory mock mode so tests and local development work immediately without credentials).*

4. **Run the backend tests**:
   ```bash
   pytest -v tests/
   ```

5. **Start the FastAPI server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Verify health:
   ```bash
   curl http://localhost:8000/health
   # Returns: {"status": "ok"}
   ```

---

### Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Configure Environment Variables**:
   Copy `.env.example` to `.env.local`:
   ```bash
   cp .env.example .env.local
   ```
   Fill in your Vapi credentials:
   ```env
   NEXT_PUBLIC_VAPI_PUBLIC_KEY="your-vapi-public-key"
   NEXT_PUBLIC_VAPI_ASSISTANT_ID="your-vapi-assistant-id"
   NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"
   ```

4. **Run the Next.js development server**:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## 5. Google Calendar OAuth 2.0 Setup

To connect live Google Calendar operations:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Calendar API**.
3. Under **OAuth consent screen**, set user type to **External** and add `https://www.googleapis.com/auth/calendar.events` scope. Add your Google account as a Test User.
4. Under **Credentials**, create an **OAuth Client ID** (Web application).
5. Generate a Refresh Token using the Google OAuth2 playground or your preferred authorization flow with offline access.
6. Populate the `.env` file in `backend/`:
   ```env
   GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   GOOGLE_CLIENT_SECRET="your-client-secret"
   GOOGLE_REFRESH_TOKEN="your-refresh-token"
   GOOGLE_CALENDAR_ID="primary"
   ```

---

## 6. Vapi Assistant Configuration

1. Log in to [Vapi](https://vapi.ai).
2. Create a new Assistant:
   - **Transcriber**: Deepgram (`nova-2`, English)
   - **Voice**: Cartesia (`248be419-c632-4f23-adf1-5324ed7dbf10` or ElevenLabs)
   - **Model**: OpenAI (`gpt-4o` or `gpt-4o-mini`)
   - **System Prompt**: Paste the contents of `prompts/system-prompt.txt`.
3. Add the two Custom Tools pointing to your public backend URL (e.g. ngrok or deployed FastAPI service):
   - **`check_availability`**: `POST {{API_BASE_URL}}/api/calendar/availability`
   - **`book_meeting`**: `POST {{API_BASE_URL}}/api/calendar/book`
   *(Refer to `vapi-assistant-config.json` for the exact tool schemas).*

---

## 7. API Endpoints Reference

### `GET /health`
Returns the status of the FastAPI backend.
```json
{
  "status": "ok"
}
```

### `POST /api/calendar/availability`
Queries available 30-minute meeting slots.
**Request**:
```json
{
  "date": "2026-09-15",
  "timezone": "Asia/Manila"
}
```
**Response**:
```json
{
  "success": true,
  "date": "2026-09-15",
  "timezone": "Asia/Manila",
  "available_slots": [
    {
      "start": "2026-09-15T09:00:00+08:00",
      "end": "2026-09-15T09:30:00+08:00",
      "display_time": "9:00 AM - 9:30 AM"
    }
  ],
  "count": 1
}
```

### `POST /api/calendar/book`
Reserves a verified slot in Google Calendar.
**Request**:
```json
{
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "timezone": "Asia/Manila",
  "start": "2026-09-15T09:00:00+08:00",
  "end": "2026-09-15T09:30:00+08:00"
}
```
**Response (Success)**:
```json
{
  "success": true,
  "event_id": "google_event_id_xyz",
  "message": "Meeting successfully booked for Jane Smith.",
  "start": "2026-09-15T09:00:00+08:00",
  "end": "2026-09-15T09:30:00+08:00"
}
```
**Response (Slot Taken Conflict)**:
```json
{
  "success": false,
  "reason": "TIME_UNAVAILABLE",
  "message": "The requested time slot was just taken. Please choose another available time."
}
```

---

## 8. Deployment

- **Frontend**: Deploy `frontend/` to **Vercel** with environment variables `NEXT_PUBLIC_VAPI_PUBLIC_KEY`, `NEXT_PUBLIC_VAPI_ASSISTANT_ID`, and `NEXT_PUBLIC_API_BASE_URL`.
- **Backend**: Deploy `backend/` as a Docker container or Python web service on **Render**, **Fly.io**, or **Railway** with the Google OAuth environment variables and `ALLOWED_ORIGINS`.
