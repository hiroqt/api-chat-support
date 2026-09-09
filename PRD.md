# BrainCX AI Voice Agent

## Product Requirements Document (PRD)

**Project:** BrainCX AI Voice Agent
**Assessment:** Junior Solution Engineer — BrainCX AI Inc.
**Version:** 1.0
**Status:** Implementation Ready
**Primary Goal:** Build a natural web-based voice agent that represents BrainCX, understands visitor needs, and reliably checks and books meetings through a live Google Calendar.

---

# 1. Product Overview

The BrainCX AI Voice Agent is a web-based conversational voice experience for the BrainCX website.

The agent has two primary responsibilities:

1. Explain BrainCX accurately using only approved information.
2. Help qualified visitors schedule a meeting by checking live Google Calendar availability and creating a calendar event.

The experience should feel like a capable human representative rather than a scripted chatbot.

The system will use:

```text
Next.js
Vapi
FastAPI
Google Calendar API
```

FastAPI will serve as the backend automation and business-logic layer.

No n8n workflow automation is required.

---

# 2. Problem Statement

Website visitors may have questions about BrainCX but may not immediately know:

* What BrainCX does
* Whether BrainCX is relevant to their organization
* What problems BrainCX addresses
* Whether they should speak with the team
* When they can schedule a conversation

A traditional form-based experience creates friction.

The product should provide a conversational interface that:

* Understands the visitor's situation
* Explains BrainCX naturally
* Answers approved questions
* Handles unexpected conversation
* Checks actual calendar availability
* Books meetings reliably

---

# 3. Product Goals

## Primary Goals

### G1 — Natural Conversation

The agent should:

* Listen before responding
* Handle interruptions
* Avoid robotic scripts
* Ask sensible follow-up questions
* Adapt to the visitor's responses
* Handle silence gracefully

---

### G2 — Accurate BrainCX Information

The agent must only use facts explicitly approved in the assessment.

It must not invent:

* Pricing
* Customer information
* Performance metrics
* Company statistics
* Product capabilities
* Partnerships
* Technical architecture

---

### G3 — Reliable Calendar Scheduling

The agent must support:

```text
Check availability
        ↓
Select available time
        ↓
Collect name
        ↓
Collect email
        ↓
Collect timezone
        ↓
Confirm details
        ↓
Re-check availability
        ↓
Create Google Calendar event
        ↓
Confirm successful booking
```

The event must actually appear in Google Calendar.

---

### G4 — Resilient Conversation

The agent must gracefully handle:

* Interruptions
* Silence
* Email corrections
* Invalid email input
* Date changes
* Time changes
* Booking cancellation
* Calendar conflicts
* Unknown questions
* Off-topic questions

---

# 4. Non-Goals

The following are intentionally outside the scope:

* User accounts
* Authentication for website visitors
* Database persistence
* CRM integration
* Payment processing
* Customer support ticketing
* Complex analytics platform
* RAG/vector database
* Multi-agent architecture
* Phone number integration
* Human workforce replacement workflows

The goal is a focused technical assessment implementation.

---

# 5. Target User

The primary user is a BrainCX website visitor who may be:

* Evaluating BrainCX
* Interested in AI-powered customer experience
* Working in one of BrainCX's target verticals
* Interested in learning more
* Interested in speaking with the BrainCX team

---

# 6. User Experience

The visitor opens the website and sees a voice interaction.

Example:

```text
Visitor
   ↓
Starts voice conversation
   ↓
Agent introduces itself naturally
   ↓
Visitor explains their situation
   ↓
Agent asks relevant questions
   ↓
Agent explains relevant BrainCX capabilities
   ↓
Visitor wants to speak with the team
   ↓
Agent checks availability
   ↓
Visitor selects a time
   ↓
Agent collects booking information
   ↓
Agent confirms details
   ↓
FastAPI checks calendar again
   ↓
Google Calendar event created
   ↓
Agent confirms booking
```

---

# 7. Functional Requirements

## FR-001 — Voice Interaction

The application shall provide a browser-based voice interaction.

Requirements:

* No phone number
* Microphone-based interaction
* Start conversation
* End conversation
* Handle connection errors
* Support natural interruptions

---

## FR-002 — BrainCX Explanation

The agent shall explain BrainCX using only approved reference facts.

The agent should adapt explanations based on the visitor's context instead of delivering a fixed company script.

---

## FR-003 — Discovery

The agent shall ask sensible questions when appropriate.

Example topics:

* Organization type
* Customer conversation challenges
* Existing agent capacity
* Operational challenges
* Interest in learning more

Questions must feel conversational rather than like a questionnaire.

---

## FR-004 — Live Availability

The agent shall check actual Google Calendar availability.

The availability flow must use:

```text
Vapi
  ↓
FastAPI
  ↓
Google Calendar API
```

Availability must never be hard-coded.

---

## FR-005 — Meeting Booking

The agent shall create a Google Calendar event containing:

* Visitor name
* Visitor email
* Requested date/time
* Timezone

The event must be successfully created before the agent claims the booking is complete.

---

## FR-006 — Email Confirmation

The agent shall confirm the interpreted email address before booking.

If the visitor corrects it, the corrected value becomes authoritative.

---

## FR-007 — Timezone

The agent shall collect or infer the visitor's timezone.

Internally, the system should use IANA timezone identifiers.

Examples:

```text
Asia/Manila
America/New_York
America/Los_Angeles
Europe/London
```

---

## FR-008 — Booking Conflict Handling

The system shall re-check availability immediately before creating the calendar event.

If the requested time is no longer available:

```text
Do not create event
        ↓
Return conflict
        ↓
Agent explains naturally
        ↓
Offer another time
```

---

## FR-009 — Intent Changes

The agent must respect the visitor's latest intent.

Example:

```text
Visitor:
"Book Tuesday."

Agent:
"Sure..."

Visitor:
"Actually, Thursday is better."

Agent:
"Of course. Let me check Thursday."
```

The previous Tuesday selection must be discarded.

---

## FR-010 — Cancellation

If the visitor decides not to book:

```text
Visitor:
"Never mind."

Agent:
"No problem."
```

The booking tool must not be called.

---

## FR-011 — Unknown Information

When asked something outside the approved knowledge:

> "I don't have that information, but I can connect you with someone from the team."

The agent must not hallucinate an answer.

---

## FR-012 — Off-Topic Questions

The agent should respond naturally without breaking character.

Example:

> "I don't have information about that. I can help with BrainCX or arrange a conversation with the team."

The agent must not read a list of capabilities.

---

# 8. Approved BrainCX Knowledge

## Positioning

BrainCX is:

> The AI CX Operator for high consequence verticals.

BrainCX redesigns, builds, and runs customer conversations.

Powered by AI, managed by BrainCX.

---

## Background

Founded in 2021 by:

* Tariq Alinur
* Rose Flores

Headquartered in:

* West Palm Beach, Florida

Tariq spent three decades running contact centre operations at:

* Apple
* JPMorgan Chase
* American Express
* Liberty Latin America
* Spirit Airlines

---

## Approach

BrainCX clones a client's best agents, including:

* Voice
* Empathy
* Objection handling

The system deploys that capability at scale.

The platform gives existing agents more capacity.

It does not replace them.

---

## Verticals

### Higher Education

200% enrollment lift across 5 universities.

### Healthcare

40% bilingual booking lift.

### Telecom

35% AHT reduction.

---

## Commercial

Outcome-based pricing that follows performance, never per seat.

Compliance included at no additional cost:

* HIPAA
* SOC 2 Type II
* PCI DSS
* GDPR

Additional approved information:

* 99.9% uptime SLA
* Live in 4 to 6 weeks
* Patent-pending
* braincx.com

---

# 9. Approved Figures

The following figures may be quoted:

```text
31% contact rate against a 5% baseline.
98% self-service resolution.
Sub-300ms response.
Fewer than 1% of callers have ever asked whether they were speaking with AI.
```

No other performance figures should be introduced.

---

# 10. Prohibited Claims

The agent must never describe BrainCX as:

* A headcount reduction solution
* An employee replacement
* A way to eliminate agents
* A replacement for human workers

The correct positioning is:

> The platform gives existing agents more capacity. It does not replace them.

---

# 11. Conversation Requirements

## Turn Taking

The agent should:

* Allow the visitor to finish
* Stop speaking when interrupted
* Respond to the latest input
* Avoid unnecessary monologues

---

## Silence

The agent should allow reasonable silence before prompting the visitor.

Avoid repeatedly saying:

> "Are you there?"

---

## Corrections

Corrections should be accepted without friction.

Example:

> "Actually, that's not my email."

Agent:

> "No problem. What should I use instead?"

---

# 12. Booking Requirements

Required booking fields:

```text
name
email
timezone
start
end
```

Booking must follow:

```text
Collect
   ↓
Validate
   ↓
Confirm
   ↓
Check availability
   ↓
Re-check
   ↓
Create
   ↓
Verify response
   ↓
Confirm to visitor
```

---

# 13. Technical Requirements

## Frontend

Use:

```text
Next.js
TypeScript
```

Responsibilities:

* Voice interface
* Vapi integration
* Connection state
* Error presentation
* Basic interaction UI

---

## Voice Platform

Use:

```text
Vapi
```

Responsibilities:

* Speech-to-text
* LLM conversation
* Text-to-speech
* Tool invocation
* Interruption handling

---

## Backend

Use:

```text
FastAPI
Python
Pydantic
```

Responsibilities:

* Tool endpoints
* Request validation
* Calendar business logic
* Timezone handling
* Availability checks
* Booking creation
* Error handling

---

## Calendar

Use:

```text
Google Calendar API
```

Google Calendar is the authoritative source of availability.

---

# 14. API Requirements

## Availability

```http
POST /api/calendar/availability
```

Request:

```json
{
  "date": "YYYY-MM-DD",
  "timezone": "Asia/Manila"
}
```

---

## Booking

```http
POST /api/calendar/book
```

Request:

```json
{
  "name": "John Smith",
  "email": "john@example.com",
  "timezone": "Asia/Manila",
  "start": "ISO_DATETIME",
  "end": "ISO_DATETIME"
}
```

---

# 15. Error Requirements

The system must distinguish between:

```text
Validation failure
Calendar unavailable
Requested time unavailable
Authentication failure
Google API failure
Unexpected server failure
```

The visitor should receive natural language rather than technical error messages.

---

# 16. Security Requirements

Secrets must remain server-side.

Never expose:

* Google credentials
* Google access tokens
* Private API keys
* Service account credentials
* Backend secrets

The frontend must only receive client-safe configuration.

---

# 17. Performance Requirements

The system should prioritize low conversational latency.

The implementation should avoid unnecessary network hops.

Preferred:

```text
Vapi → FastAPI → Google Calendar
```

rather than:

```text
Vapi → automation platform → another API → another service → Calendar
```

---

# 18. Deployment

Target architecture:

```text
Frontend
Vercel
   │
   ▼
Vapi

Backend
FastAPI hosting
   │
   ▼
Google Calendar API
```

The exact FastAPI hosting provider may be selected based on available free-tier options.

---

# 19. Testing Requirements

Before submission, manually test:

### Conversation

* Normal conversation
* BrainCX explanation
* Discovery
* Unknown question
* Off-topic question
* Interruption
* Silence

### Booking

* Available slot
* Unavailable slot
* Date change
* Time change
* Email correction
* Invalid email
* Timezone
* Booking cancellation
* Calendar conflict
* Calendar API failure

### Final Verification

Every successful booking must be verified directly in Google Calendar.

---

# 20. Success Criteria

The project is successful when an evaluator can:

1. Open the public web widget.
2. Start a natural voice conversation.
3. Ask unexpected questions.
4. Interrupt the agent.
5. Correct information.
6. Request a meeting.
7. Hear actual availability.
8. Select a time.
9. Provide name, email, and timezone.
10. Successfully create a real Google Calendar event.

---

# 21. Assessment Alignment

| Assessment Area        | Weight | Product Priority |
| ---------------------- | -----: | ---------------- |
| Conversational quality |    40% | Highest          |
| Prompt engineering     |    30% | Highest          |
| Booking reliability    |    20% | Critical         |
| Loom                   |    10% | Supporting       |

The project should optimize for these criteria rather than unnecessary technical complexity.

---

# 22. Automatic Fail Prevention

The implementation must avoid:

```text
❌ Standard AI disclaimers
❌ Reading menu options aloud
❌ Fake calendar availability
❌ Failed calendar writes
❌ Unsupported BrainCX claims
❌ Describing BrainCX as reducing headcount
❌ Paid services
```

---

# 23. Optional Extension

Only implement one extension if the core system is already reliable.

Recommended:

## Booking Confirmation

After a successful booking, provide a concise confirmation.

Example:

> "You're all set. I've booked the meeting for Tuesday at 10 AM Manila time."

Do not claim confirmation until the backend confirms the calendar event was created.

---

# 24. Definition of Done

The product is complete when:

```text
Frontend working
        +
Vapi working
        +
FastAPI working
        +
Google Calendar working
        +
Availability verified
        +
Booking verified
        +
Prompt tested
        +
Edge cases tested
        +
Public deployment working
        +
System prompt documented
        +
Loom recorded
```

---

# 25. Guiding Product Principle

> Build the smallest system that can behave like a capable BrainCX representative and reliably complete a real booking.

Conversational quality comes before feature count.

Reliability comes before visual polish.

Accuracy comes before improvisation.
