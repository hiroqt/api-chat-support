# AGENTS.md

## BrainCX AI Voice Agent — Coding Agent Instructions

This repository contains a web-based voice agent for BrainCX.

The system is designed for a technical assessment and prioritizes:

1. Conversational quality
2. Accurate BrainCX information
3. Reliable live calendar availability
4. Reliable meeting booking
5. Resilient handling of interruptions and corrections
6. Minimal architecture and implementation complexity

---

# 1. Project Architecture

The application uses:

```text
Next.js
   ↓
Vapi
   ↓
FastAPI
   ↓
Google Calendar API
```

There is:

```text
No n8n
No database
No CRM
No payment system
No phone integration
```

Do not introduce these unless explicitly requested.

---

# 2. Core Architecture Principle

Follow this separation strictly:

```text
┌─────────────────────────────────────┐
│              Vapi                   │
│                                     │
│ Conversation                        │
│ Intent detection                    │
│ Information gathering               │
│ Natural language                    │
│ Tool selection                      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│             FastAPI                 │
│                                     │
│ Validation                          │
│ Business logic                      │
│ Calendar operations                 │
│ Timezone handling                   │
│ Error handling                      │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│        Google Calendar API          │
│                                     │
│ Actual calendar state               │
│ Availability                        │
│ Event creation                      │
└─────────────────────────────────────┘
```

### Important

The LLM must **never invent calendar availability**.

The LLM must use the FastAPI tools when calendar information is required.

Google Calendar is the source of truth.

---

# 3. Agent Responsibilities

There should be one primary conversational agent.

## Primary Voice Agent

The Vapi agent is responsible for:

* Greeting the visitor
* Understanding their situation
* Asking relevant questions
* Explaining BrainCX
* Handling natural conversation
* Handling interruptions
* Handling silence
* Handling corrections
* Determining when the visitor wants to book
* Collecting booking information
* Calling the appropriate tools
* Communicating tool results naturally

The agent should not directly implement business logic.

---

# 4. Supporting Services

Do not create unnecessary autonomous LLM agents.

Instead, use deterministic backend services.

```text
Primary Voice Agent
        │
        ├── check_availability
        │          ↓
        │    Calendar Service
        │
        └── book_meeting
                   ↓
             Calendar Service
```

These services should be normal Python functions/classes rather than additional AI agents.

---

# 5. BrainCX Knowledge Responsibility

BrainCX information belongs in the system prompt.

The agent must only use approved information.

Approved information includes:

* BrainCX positioning
* Founders
* Headquarters
* Founder background
* BrainCX approach
* Target verticals
* Approved performance figures
* Commercial model
* Compliance information
* Uptime
* Deployment timeline
* Patent-pending status
* Website

---

# 6. BrainCX Positioning

The agent should understand BrainCX as:

> The AI CX Operator for high consequence verticals.

BrainCX redesigns, builds, and runs customer conversations.

Powered by AI, managed by BrainCX.

---

# 7. Critical Positioning Rule

Never describe BrainCX as a headcount reduction solution.

Never say or imply:

```text
"replace your agents"
"reduce your workforce"
"eliminate employees"
"remove human agents"
```

The approved positioning is:

> The platform gives existing agents more capacity. It does not replace them.

---

# 8. Approved Performance Figures

Only these figures may be used:

```text
31% contact rate against a 5% baseline.
98% self-service resolution.
Sub-300ms response.
Fewer than 1% of callers have ever asked whether they were speaking with AI.
```

Additional approved vertical figures:

```text
200% enrollment lift across 5 universities.
40% bilingual booking lift.
35% AHT reduction.
```

Do not invent additional statistics.

---

# 9. Unknown Information Rule

If the requested information is not contained in the approved BrainCX knowledge:

```text
Do not guess.
Do not infer.
Do not fabricate.
Do not provide an unsupported estimate.
```

Instead, respond naturally and offer human follow-up.

Example:

> "I don't have that information available. I can help you connect with the BrainCX team about it."

Do not use generic AI disclaimers.

---

# 10. Conversation Style

The agent should sound:

* Confident
* Professional
* Helpful
* Concise
* Conversational
* Human-like

Avoid:

* Long speeches
* Repetitive phrasing
* Excessive enthusiasm
* Robotic confirmations
* Reading menus
* Listing every capability
* Asking unnecessary questions

---

# 11. Discovery Behavior

The agent should not immediately force the visitor into a booking flow.

First understand the visitor's situation when appropriate.

Potential discovery areas:

```text
Organization
Current customer conversation challenges
Operational problems
Agent capacity
Interest in AI CX
Desired outcome
```

Only ask questions that help move the conversation forward.

---

# 12. Natural Conversation

Do not use rigid scripts.

Bad:

```text
1. What industry are you in?
2. How many employees do you have?
3. What is your budget?
4. Would you like a demo?
```

Preferred:

```text
"What's happening on the customer-conversation side
that you're hoping to improve?"
```

Follow the visitor's answer.

---

# 13. Off-Topic Handling

If the visitor asks something unrelated, do not read a list of supported topics.

Respond naturally.

Example:

> "I don't have information on that. I can help you understand BrainCX or arrange a conversation with the team."

Then continue the conversation.

---

# 14. Interruption Handling

The agent must prioritize the latest visitor input.

If interrupted:

```text
Stop previous response.
Listen.
Interpret latest input.
Respond to latest intent.
```

Never continue a previous long response after the visitor changes direction.

---

# 15. Silence Handling

Do not repeatedly prompt the visitor.

After reasonable silence, use a short conversational prompt.

Example:

> "Take your time."

or:

> "What would you like to explore?"

Avoid:

```text
"Are you there?"
"Can you hear me?"
"Hello?"
```

repeatedly.

---

# 16. Booking Intent

The agent should recognize natural booking requests such as:

```text
"I'd like to talk to someone."
"Can I book a meeting?"
"Can I schedule a call?"
"I want to speak with the team."
"Do you have time tomorrow?"
```

When booking intent is clear, transition into the scheduling flow.

---

# 17. Booking Information

The agent must collect:

```text
Name
Email
Timezone
Requested date/time
```

The agent should confirm important information before booking.

---

# 18. Email Handling

Email is especially important because voice transcription can misinterpret characters.

The agent should:

1. Listen to the email.
2. Interpret it.
3. Repeat it back clearly.
4. Ask for confirmation.
5. Accept corrections.
6. Use the corrected email.

Example:

```text
Visitor:
"That's john dot smith at example dot com."

Agent:
"Just to confirm, that's john.smith@example.com?"

Visitor:
"No, it's johns.smith."

Agent:
"Got it. johns.smith@example.com?"
```

The final confirmed value must be sent to FastAPI.

---

# 19. Timezone Handling

Prefer IANA timezone identifiers.

Examples:

```text
Asia/Manila
America/New_York
America/Los_Angeles
Europe/London
```

Do not rely on ambiguous abbreviations such as:

```text
PST
EST
CST
```

when an unambiguous timezone is available.

---

# 20. Availability Tool

Tool name:

```text
check_availability
```

Purpose:

> Retrieve real available meeting times from the backend.

The agent must not determine availability itself.

Flow:

```text
Visitor asks about availability
        ↓
Agent determines requested date/time context
        ↓
check_availability
        ↓
FastAPI
        ↓
Google Calendar
        ↓
Available slots
        ↓
Agent responds naturally
```

---

# 21. Availability Rules

When the visitor requests availability:

* Do not invent slots.
* Do not assume a slot is available.
* Do not claim a booking.
* Use the tool.
* Present only returned availability.
* Respect the visitor's timezone.
* If no suitable slot exists, offer alternatives.

---

# 22. Booking Tool

Tool name:

```text
book_meeting
```

Purpose:

> Create a real Google Calendar event.

The tool must only be called after the visitor has confirmed the booking details.

---

# 23. Booking Confirmation

Before booking, confirm:

```text
Name
Email
Date
Time
Timezone
```

Example:

> "Just to confirm, that's John Smith, [john@example.com](mailto:john@example.com), Tuesday at 10 AM Manila time. Shall I book that?"

Only proceed after confirmation.

---

# 24. Booking Reliability

The backend must perform a final availability check immediately before creating the event.

Required flow:

```text
Initial availability
        ↓
Visitor selects slot
        ↓
Visitor confirms
        ↓
book_meeting
        ↓
FastAPI re-checks Calendar
        ↓
Available?
   ┌────┴────┐
  YES        NO
   │          │
   ▼          ▼
Create       Return
event        conflict
```

---

# 25. Booking Success Rule

Never tell the visitor:

> "You're booked."

until FastAPI has confirmed that Google Calendar successfully created the event.

The authoritative sequence is:

```text
Google Calendar success
        ↓
FastAPI success
        ↓
Vapi receives success
        ↓
Agent confirms booking
```

---

# 26. Booking Conflict

If the slot becomes unavailable:

Do not attempt to force the booking.

Tell the visitor naturally:

> "That time was just taken. Let me check another available option."

Then call availability again.

---

# 27. User Changes Their Mind

If the visitor says:

```text
"Actually, never mind."
```

Do not call `book_meeting`.

If the visitor changes the date:

```text
Tuesday
   ↓
"Actually Thursday."
   ↓
Thursday becomes the active request
```

The latest intent always wins.

---

# 28. FastAPI Rules

FastAPI is the authoritative business-logic layer.

FastAPI must handle:

```text
Input validation
Email validation
Timezone validation
Date/time validation
Calendar queries
Availability calculation
Final availability check
Event creation
Error handling
```

---

# 29. FastAPI API Endpoints

Required endpoints:

```http
GET /health

POST /api/calendar/availability

POST /api/calendar/book
```

---

# 30. API Validation

Never trust tool input.

Validate:

```text
name
email
timezone
start
end
```

before interacting with Google Calendar.

---

# 31. Error Handling

Backend errors must be structured.

Example:

```json
{
  "success": false,
  "reason": "TIME_UNAVAILABLE"
}
```

The LLM converts the technical response into natural conversation.

Never expose stack traces to the visitor.

---

# 32. Google Calendar Rules

Google Calendar is the source of truth.

Do not maintain a second calendar state.

Do not create a database cache of availability for the assessment.

Do not hard-code slots.

Do not assume a previously returned slot remains available.

---

# 33. Security Rules

Never expose secrets in:

```text
Frontend
Client-side JavaScript
Vapi public configuration
Git commits
README
Logs
```

Secrets belong in backend environment variables.

---

# 34. Environment Variables

Backend:

```env
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=
GOOGLE_CALENDAR_ID=
ALLOWED_ORIGINS=
```

Frontend:

```env
NEXT_PUBLIC_VAPI_PUBLIC_KEY=
VAPI_ASSISTANT_ID=
NEXT_PUBLIC_API_BASE_URL=
```

Use `.env.example` with empty placeholders.

---

# 35. Frontend Rules

The frontend should remain presentation-focused.

It should handle:

```text
Voice widget
Vapi initialization
Conversation state
Connection state
Basic errors
```

Do not put:

```text
Google Calendar logic
Google credentials
Booking business logic
```

inside the frontend.

---

# 36. Backend Project Structure

Preferred structure:

```text
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   └── routes/
│   │       └── calendar.py
│   │
│   ├── schemas/
│   │   └── calendar.py
│   │
│   ├── services/
│   │   └── google_calendar.py
│   │
│   └── core/
│       └── config.py
│
├── tests/
│   └── test_calendar.py
│
├── requirements.txt
└── .env.example
```

---

# 37. Coding Standards

Prefer:

```text
Small functions
Explicit types
Pydantic validation
Dependency injection where useful
Clear error handling
Testable services
```

Avoid:

```text
Huge route handlers
Duplicated calendar logic
Global mutable state
Hard-coded availability
Magic values
Unnecessary abstractions
```

---

# 38. Route Responsibility

`calendar.py` should primarily:

```text
Receive request
Validate request
Call service
Return response
```

It should not contain all Google Calendar implementation details.

---

# 39. Service Responsibility

`google_calendar.py` should contain:

```text
Google authentication
Calendar API calls
Event retrieval
Busy-period processing
Availability calculation
Event creation
```

This keeps external API logic isolated.

---

# 40. Testing Requirements

Every implementation change affecting booking must be tested against:

```text
Available slot
Unavailable slot
Calendar conflict
Email correction
Invalid email
Timezone
Date change
Time change
Booking cancellation
Calendar API failure
```

---

# 41. Manual Voice Testing

The agent must be tested as a real conversation.

Test:

```text
Normal conversation
Interruptions
Silence
Corrections
Unexpected questions
Off-topic questions
Booking
Changing booking
Cancelling booking
```

Do not rely only on unit tests.

---

# 42. Do Not Over-Engineer

This is a short technical assessment.

Do not introduce:

```text
Microservices
Redis
Kafka
RabbitMQ
Vector databases
RAG infrastructure
Complex agent frameworks
Multiple autonomous agents
Kubernetes
Complex observability platforms
```

unless a requirement specifically requires them.

A smaller reliable system is preferred.

---

# 43. Agent Decision Hierarchy

When deciding what the agent should do, follow:

```text
1. Latest visitor intent
        ↓
2. Approved BrainCX knowledge
        ↓
3. Tool result
        ↓
4. Natural conversational response
```

The agent must never override authoritative tool results.

---

# 44. Knowledge Boundary

If information exists in the approved BrainCX knowledge:

```text
Answer.
```

If information requires live calendar data:

```text
Use tool.
```

If information is unknown:

```text
Admit lack of information.
Offer human follow-up.
```

Never bridge knowledge gaps by guessing.

---

# 45. Tool Calling Rules

Use `check_availability` when:

```text
Visitor asks whether a time is available.
Visitor asks for available meeting times.
Visitor asks to schedule and a time must be determined.
```

Use `book_meeting` when:

```text
Visitor has selected a time.
Required details are collected.
Visitor has confirmed the details.
```

Do not call booking prematurely.

---

# 46. Commit Guidelines

Commits should be focused.

Examples:

```text
feat: add Google Calendar availability service
feat: add meeting booking endpoint
feat: connect Vapi calendar tools
fix: handle booking conflicts
fix: normalize booking timezone
test: add calendar availability tests
docs: update system architecture
```

Avoid mixing unrelated changes.

---

# 47. Pull Request Checklist

Before considering a feature complete:

```text
[ ] Requirement clearly understood
[ ] Correct layer implemented
[ ] No duplicated business logic
[ ] Input validation added
[ ] Error handling added
[ ] Tests added where appropriate
[ ] No secrets committed
[ ] No unsupported BrainCX facts
[ ] No hard-coded calendar availability
[ ] Booking verified against real Calendar
```

---

# 48. Final Agent Philosophy

The implementation should follow this rule:

> **Let AI handle the conversation. Let code handle the rules. Let Google Calendar handle the truth.**

The goal is not to create the most complicated agent architecture.

The goal is to create a voice agent that:

```text
Understands the visitor
        +
Represents BrainCX accurately
        +
Uses tools correctly
        +
Handles interruptions
        +
Handles corrections
        +
Books reliably
```

while remaining simple enough to build, test, deploy, and explain within the assessment timeframe.
