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
- **Interactive Real-Time Meeting Pass**: Synchronously manifests an enterprise-grade confirmation hub upon booking, featuring Google Meet room launch, dual-timezone display (Visitor Local Time vs. BrainCX West Palm Beach FL HQ), 1-click RFC 5545 `.ics` download, Google Calendar sync, and instant confirmation re-dispatch.
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

### `GET /api/calendar/event/{event_id}.ics`
Streams an RFC 5545 compliant `.ics` iCalendar attachment for 1-click import into macOS Calendar, Google Calendar, Apple Calendar, or Outlook.
**Response Header**:
```http
Content-Type: text/calendar; charset=utf-8
Content-Disposition: attachment; filename="braincx-meeting-{event_id}.ics"
```

### `GET /api/calendar/event/{event_id}`
Returns complete structured `MeetingPassDetails` including dual-timezone calculations (`visitor_formatted_time` and `braincx_formatted_time`), Google Meet URL, and direct Google Calendar URLs.

### `POST /api/calendar/resend-confirmation`
Re-dispatches booking confirmation email and calendar invitation to attendee.
**Request**:
```json
{
  "event_id": "google_event_id_xyz",
  "email": "jane.smith@example.com"
}
```
**Response**:
```json
{
  "success": true,
  "event_id": "google_event_id_xyz",
  "email": "jane.smith@example.com",
  "message": "Confirmation email and calendar invitation successfully resent to jane.smith@example.com.",
  "dispatched_at": "2026-09-10T04:15:00Z"
}
```

---

## 8. Production Architecture & Hardening

The production system includes full enterprise hardening:

- **Vapi Shared Secret Authentication**: All tool endpoints require `X-Vapi-Secret` or `Authorization: Bearer <token>` matching `VAPI_SECRET_TOKEN`.
- **Google Meet Conferencing**: Auto-generates Google Meet video links (`conferenceDataVersion=1`) and sends real attendee invites via `sendUpdates="all"`.
- **Concurrency Mutex**: Thread-safe locking prevents race condition double-bookings across concurrent requests during the pre-check window.
- **Production Probes**:
  - `GET /health/live`: Fast container liveness check.
  - `GET /health/ready`: Deep readiness probe checking Google Calendar credentials and service connectivity.
- **Call Telemetry**: Ingests Vapi `end-of-call-report` webhooks at `POST /api/calendar/call-summary` with call duration, transcript snippet, and recording status.
- **Structured JSON Logging**: Standardized JSON formatting for Datadog, CloudWatch, GCP Cloud Logging, and BetterStack.
- **Microphone Pre-Flight Probes**: Front-end checks browser microphone permissions before WebRTC initiation to provide clear guided prompts.
- **CI/CD Pipeline**: GitHub Actions workflow (`.github/workflows/ci.yml`) testing Python 3.11 pytest, Next.js build, and Docker build.

---

## 9. Production Deployment Guide

### Option A: Docker Container Deployment (GCP Cloud Run / AWS ECS / Railway / Fly.io)

1. **Build and test the Docker container locally**:
   ```bash
   cd backend
   docker build -t braincx-voice-agent-backend:latest .
   docker run -p 8000:8000 --env-file .env braincx-voice-agent-backend:latest
   ```

2. **Deploy with Docker Compose**:
   ```bash
   cd backend
   docker compose up -d
   ```

3. **Deploying to Google Cloud Run (Recommended)**:
   ```bash
   # Authenticate and submit build to GCP Artifact Registry
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/braincx-voice-agent-backend

   # Deploy container with environment variables
   gcloud run deploy braincx-voice-agent-backend \
     --image gcr.io/YOUR_PROJECT_ID/braincx-voice-agent-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ENVIRONMENT=production,ENABLE_MOCK_FALLBACK=false,ALLOWED_ORIGINS="https://voice.braincx.com" \
     --set-secrets GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,GOOGLE_REFRESH_TOKEN=google-refresh-token:latest,VAPI_SECRET_TOKEN=vapi-secret-token:latest
   ```

4. **Deploying to Railway or Render**:
   - Connect your GitHub repository (`api-chat-support`).
   - Select `backend` as the root directory.
   - The platform will auto-detect the `backend/Dockerfile`.
   - Add environment variables (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`, `VAPI_SECRET_TOKEN`, `ENVIRONMENT=production`).

---

### Option B: Frontend Deployment (Vercel)

1. Connect your repository to [Vercel](https://vercel.com).
2. Set Root Directory to `frontend`.
3. Add Production Environment Variables:
   ```env
   NEXT_PUBLIC_VAPI_PUBLIC_KEY="your-vapi-public-key"
   NEXT_PUBLIC_VAPI_ASSISTANT_ID="your-vapi-assistant-id"
   NEXT_PUBLIC_API_BASE_URL="https://your-backend-service.run.app"
   ```
4. Deploy. Assign your custom production domain (e.g. `voice.braincx.com`).

---

## 10. Pushing Your Code to GitHub

To push your local commits to your GitHub repository (`hiroqt/api-chat-support`):

```bash
# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

