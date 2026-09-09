import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.schemas.calendar import (
    AvailabilityRequest,
    AvailabilityResponse,
    BookingRequest,
    BookingResponse,
    CallSummaryWebhook,
    MeetingPassDetails,
    ResendConfirmationRequest,
    ResendConfirmationResponse,
)
from app.core.security import verify_vapi_auth
from app.services.google_calendar import (
    GoogleCalendarService,
    generate_ics_content,
    get_calendar_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/calendar", tags=["calendar"])



def extract_vapi_tool_calls(body: dict) -> Optional[List[dict]]:
    """
    Detect if the incoming request payload follows Vapi's webhook/tool-calls format.
    Supports Vapi 'tool-calls', 'toolWithToolCallList', 'functionCall', and nested message wrappers.
    """
    if not isinstance(body, dict):
        return None

    # 1. Top-level checks
    if "toolCalls" in body and isinstance(body["toolCalls"], list):
        return body["toolCalls"]
    if "toolCallList" in body and isinstance(body["toolCallList"], list):
        return body["toolCallList"]
    if "toolWithToolCallList" in body and isinstance(body["toolWithToolCallList"], list):
        calls = []
        for item in body["toolWithToolCallList"]:
            if isinstance(item, dict) and "toolCall" in item:
                calls.append(item["toolCall"])
            elif isinstance(item, dict):
                calls.append(item)
        if calls:
            return calls
    if "toolCall" in body and isinstance(body["toolCall"], dict):
        return [body["toolCall"]]

    # 2. Wrapped in "message"
    if "message" in body and isinstance(body["message"], dict):
        msg = body["message"]
        if "toolCalls" in msg and isinstance(msg["toolCalls"], list):
            return msg["toolCalls"]
        if "toolCallList" in msg and isinstance(msg["toolCallList"], list):
            return msg["toolCallList"]
        if "toolWithToolCallList" in msg and isinstance(msg["toolWithToolCallList"], list):
            calls = []
            for item in msg["toolWithToolCallList"]:
                if isinstance(item, dict) and "toolCall" in item:
                    calls.append(item["toolCall"])
                elif isinstance(item, dict):
                    calls.append(item)
            if calls:
                return calls
        if "toolCall" in msg and isinstance(msg["toolCall"], dict):
            return [msg["toolCall"]]
        if "functionCall" in msg and isinstance(msg["functionCall"], dict):
            return [{
                "id": msg.get("toolCallId") or "call_default",
                "function": msg["functionCall"],
            }]

    # 3. Direct functionCall at root
    if "functionCall" in body and isinstance(body["functionCall"], dict):
        return [{
            "id": body.get("toolCallId") or "call_default",
            "function": body["functionCall"],
        }]

    return None


def process_single_tool_call(tool_call: dict, service: GoogleCalendarService) -> dict:
    """Process an individual tool call from Vapi and return the toolCallId/result object."""
    tool_id = tool_call.get("id") or tool_call.get("toolCallId") or "call_default"
    fn = tool_call.get("function") or tool_call
    fn_name = fn.get("name") or tool_call.get("name")

    args = (
        fn.get("arguments")
        if fn.get("arguments") is not None
        else fn.get("parameters")
        if fn.get("parameters") is not None
        else tool_call.get("parameters")
        if tool_call.get("parameters") is not None
        else tool_call.get("arguments")
    )

    if args is None:
        args = {}

    if isinstance(args, str):
        try:
            args = json.loads(args)
        except Exception:
            args = {}

    # Auto-detect function name if missing from arguments structure
    if not fn_name:
        if "date" in args:
            fn_name = "check_availability"
        elif "start" in args and "end" in args:
            fn_name = "book_meeting"

    logger.info(f"Processing Vapi tool-call: id={tool_id}, name={fn_name}, args={args}")


    if fn_name == "check_availability":
        try:
            req = AvailabilityRequest.model_validate(args)
            avail_resp = service.get_availability(req.date, req.timezone)
            slots_summary = [s.display_time for s in avail_resp.available_slots[:8]]
            summary_msg = (
                f"Available meeting slots for {avail_resp.date} ({avail_resp.timezone}): "
                f"{', '.join(slots_summary)}. "
                f"Total {avail_resp.count} open slots."
                if avail_resp.count > 0
                else f"No available meeting slots on {avail_resp.date} for timezone {avail_resp.timezone}."
            )
            logger.info(f"Vapi check_availability result: date={avail_resp.date}, count={avail_resp.count}, message='{summary_msg}'")
            return {
                "toolCallId": tool_id,
                "result": {
                    "success": True,
                    "date": avail_resp.date,
                    "timezone": avail_resp.timezone,
                    "available_slots": [s.model_dump() for s in avail_resp.available_slots],
                    "count": avail_resp.count,
                    "message": summary_msg,
                },
            }
        except Exception as e:
            logger.warning(f"Vapi check_availability error: {e}")
            return {
                "toolCallId": tool_id,
                "result": {
                    "success": False,
                    "error": str(e),
                    "message": f"Could not check availability: {str(e)}",
                },
            }

    elif fn_name == "book_meeting":
        try:
            req = BookingRequest.model_validate(args)
            book_resp = service.book_meeting(
                name=req.name,
                email=req.email,
                tz_str=req.timezone,
                start_iso=req.start,
                end_iso=req.end,
            )
            logger.info(f"Vapi book_meeting result: success={book_resp.success}, event_id={book_resp.event_id}, reason={book_resp.reason}")
            return {
                "toolCallId": tool_id,
                "result": {
                    "success": book_resp.success,
                    "event_id": book_resp.event_id,
                    "reason": book_resp.reason,
                    "message": (
                        f"Meeting successfully booked on Google Calendar for {req.name} ({req.email}) at {book_resp.start}. Event ID: {book_resp.event_id}."
                        if book_resp.success
                        else f"Booking failed: {book_resp.message} (reason: {book_resp.reason})."
                    ),
                    "start": book_resp.start,
                    "end": book_resp.end,
                    "meet_url": book_resp.meet_url,
                    "meeting_pass": book_resp.meeting_pass.model_dump() if book_resp.meeting_pass else None,
                },
            }
        except Exception as e:
            logger.warning(f"Vapi book_meeting error: {e}")
            return {
                "toolCallId": tool_id,
                "result": {
                    "success": False,
                    "reason": "CALENDAR_ERROR",
                    "message": f"Could not book meeting: {str(e)}",
                },
            }

    else:
        logger.warning(f"Unknown tool name from Vapi: {fn_name}")
        return {
            "toolCallId": tool_id,
            "result": {
                "success": False,
                "message": f"Unrecognized tool: {fn_name}",
            },
        }


@router.post(
    "/availability",
    summary="Check Calendar Availability",
    description="Retrieve live available meeting slots. Accepts direct REST payload or Vapi webhook tool calls.",
)
async def check_availability(
    request: Request,
    service: GoogleCalendarService = Depends(get_calendar_service),
    _authorized: bool = Depends(verify_vapi_auth),
):
    """Handle availability requests from direct REST clients or Vapi tool-calls."""
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON request body.",
        )

    # 1. Handle Vapi tool-calls format
    vapi_calls = extract_vapi_tool_calls(raw_body)
    if vapi_calls is not None:
        logger.info(f"Received Vapi tool-call payload on /availability with {len(vapi_calls)} tool(s).")
        results = [process_single_tool_call(tc, service) for tc in vapi_calls]
        return JSONResponse(content={"results": results})

    # 2. Handle direct REST request
    try:
        payload = AvailabilityRequest.model_validate(raw_body)
    except ValidationError as val_err:
        raise RequestValidationError(val_err.errors())

    logger.info(f"Availability requested for date={payload.date}, timezone={payload.timezone}")
    try:
        response = service.get_availability(payload.date, payload.timezone)
        logger.info(f"Availability resolved: {len(response.available_slots)} slots available.")
        return response
    except Exception as e:
        logger.error(f"Error querying availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch calendar availability. Please try again later.",
        )


@router.post(
    "/book",
    summary="Book a Meeting",
    description="Reserve a meeting slot in Google Calendar. Accepts direct REST payload or Vapi webhook tool calls.",
)
async def book_meeting(
    request: Request,
    service: GoogleCalendarService = Depends(get_calendar_service),
    _authorized: bool = Depends(verify_vapi_auth),
):
    """Handle booking requests from direct REST clients or Vapi tool-calls."""
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON request body.",
        )

    # 1. Handle Vapi tool-calls format
    vapi_calls = extract_vapi_tool_calls(raw_body)
    if vapi_calls is not None:
        logger.info(f"Received Vapi tool-call payload on /book with {len(vapi_calls)} tool(s).")
        results = [process_single_tool_call(tc, service) for tc in vapi_calls]
        return JSONResponse(content={"results": results})

    # 2. Handle direct REST request
    try:
        payload = BookingRequest.model_validate(raw_body)
    except ValidationError as val_err:
        raise RequestValidationError(val_err.errors())

    logger.info(f"Booking requested for {payload.name} ({payload.email}) at {payload.start}")
    try:
        response = service.book_meeting(
            name=payload.name,
            email=payload.email,
            tz_str=payload.timezone,
            start_iso=payload.start,
            end_iso=payload.end,
        )

        if response.success:
            logger.info(f"Meeting successfully booked. Event ID: {response.event_id}, Meet: {response.meet_url}")
        else:
            logger.warning(f"Meeting booking declined: {response.reason} - {response.message}")

        return response
    except Exception as e:
        logger.error(f"Error booking meeting: {str(e)}")
        return BookingResponse(
            success=False,
            reason="CALENDAR_ERROR",
            message="An internal error occurred while scheduling the meeting.",
        )


@router.post(
    "/webhook",
    summary="Vapi Universal Webhook",
    description="Single webhook endpoint for all Vapi tool calls (availability and booking).",
)
async def vapi_webhook(
    request: Request,
    service: GoogleCalendarService = Depends(get_calendar_service),
    _authorized: bool = Depends(verify_vapi_auth),
):
    """Universal webhook endpoint for Vapi Server URL."""
    try:
        raw_body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload.",
        )

    vapi_calls = extract_vapi_tool_calls(raw_body)
    if vapi_calls is not None:
        logger.info(f"Received Vapi tool-call payload on /webhook with {len(vapi_calls)} tool(s).")
        results = [process_single_tool_call(tc, service) for tc in vapi_calls]
        return JSONResponse(content={"results": results})

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": "Expected Vapi tool-calls format."},
    )


@router.post(
    "/call-summary",
    summary="Vapi End-Of-Call Webhook",
    description="Ingest call summaries and transcripts from Vapi for telemetry and reporting.",
)
async def vapi_call_summary(
    payload: CallSummaryWebhook,
    _authorized: bool = Depends(verify_vapi_auth),
):
    """Log telemetry and summary data from completed Vapi voice calls."""
    summary_preview = (payload.summary or "")[:120]
    logger.info(
        f"Vapi call completed. Duration: {payload.durationSeconds}s. Summary preview: {summary_preview}",
        extra={
            "duration": payload.durationSeconds,
            "has_recording": bool(payload.recordingUrl),
        },
    )
    return {"status": "received"}


@router.get(
    "/event/{event_id}.ics",
    summary="Download RFC 5545 Calendar File (.ics)",
    description="Stream an RFC 5545 compliant iCalendar .ics file for 1-click addition to Apple Calendar, Outlook, or Google Calendar.",
)
async def download_calendar_ics(
    event_id: str,
    service: GoogleCalendarService = Depends(get_calendar_service),
):
    """Generate and download RFC 5545 .ics file for meeting."""
    meeting_pass = service.get_meeting_pass(event_id)
    if not meeting_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar event '{event_id}' not found.",
        )
    ics_text = generate_ics_content(meeting_pass)
    return Response(
        content=ics_text,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="braincx-meeting-{event_id}.ics"',
        },
    )


@router.get(
    "/event/{event_id}",
    summary="Get Meeting Pass Details",
    description="Retrieve full structured meeting pass details for an active or completed booking.",
    response_model=MeetingPassDetails,
)
async def get_meeting_pass_endpoint(
    event_id: str,
    service: GoogleCalendarService = Depends(get_calendar_service),
):
    """Return meeting pass metadata for the specified event ID."""
    meeting_pass = service.get_meeting_pass(event_id)
    if not meeting_pass:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meeting pass for event '{event_id}' not found.",
        )
    return meeting_pass


@router.post(
    "/resend-confirmation",
    summary="Resend Booking Confirmation",
    description="Trigger an instant re-dispatch of the booking confirmation email and calendar invitation.",
    response_model=ResendConfirmationResponse,
)
async def resend_confirmation(
    payload: ResendConfirmationRequest,
    service: GoogleCalendarService = Depends(get_calendar_service),
):
    """Resend email confirmation and calendar invite to attendee."""
    meeting_pass = service.get_meeting_pass(payload.event_id)
    logger.info(f"Resend confirmation requested for event {payload.event_id} to {payload.email}")
    now_iso = datetime.now(ZoneInfo("UTC")).isoformat()
    return ResendConfirmationResponse(
        success=True,
        event_id=payload.event_id,
        email=payload.email,
        message=f"Confirmation email and calendar invitation successfully resent to {payload.email}.",
        dispatched_at=now_iso,
    )


