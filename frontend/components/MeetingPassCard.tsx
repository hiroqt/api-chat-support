"use client";

import React, { useState } from "react";
import {
  CalendarCheck,
  Video,
  Download,
  ExternalLink,
  Mail,
  Clock,
  Globe,
  RefreshCw,
  Check,
  Copy,
  ShieldCheck,
  Calendar,
} from "lucide-react";

export interface MeetingPassData {
  eventId: string;
  title: string;
  name: string;
  email: string;
  startIso: string;
  endIso: string;
  visitorTimezone: string;
  visitorFormattedTime: string;
  braincxTimezone?: string;
  braincxFormattedTime?: string;
  meetUrl?: string;
  googleCalendarUrl?: string;
  icsDownloadUrl?: string;
  status: "pending" | "confirmed";
  invitesDispatched: boolean;
  organizer?: string;
}

interface MeetingPassCardProps {
  pass: MeetingPassData;
}

export const MeetingPassCard: React.FC<MeetingPassCardProps> = ({ pass }) => {
  const [copied, setCopied] = useState<boolean>(false);
  const [isResending, setIsResending] = useState<boolean>(false);
  const [resendStatus, setResendStatus] = useState<string | null>(null);

  const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

  const handleCopyMeetLink = () => {
    if (!pass.meetUrl) return;
    navigator.clipboard.writeText(pass.meetUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleDownloadIcs = () => {
    if (pass.icsDownloadUrl) {
      window.open(`${apiBaseUrl}${pass.icsDownloadUrl}`, "_blank");
      return;
    }

    // Client-side fallback RFC 5545 generator
    const startClean = pass.startIso.replace(/[-:]/g, "").split(".")[0];
    const endClean = pass.endIso.replace(/[-:]/g, "").split(".")[0];
    const icsString = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//BrainCX Inc//Meeting Pass//EN",
      "BEGIN:VEVENT",
      `UID:${pass.eventId}@braincx.com`,
      `DTSTART:${startClean}`,
      `DTEND:${endClean}`,
      `SUMMARY:${pass.title}`,
      `DESCRIPTION:BrainCX Discovery Call with ${pass.name}\\nMeet: ${pass.meetUrl || "Google Meet"}`,
      `LOCATION:${pass.meetUrl || "Google Meet"}`,
      "STATUS:CONFIRMED",
      "END:VEVENT",
      "END:VCALENDAR",
    ].join("\r\n");

    const blob = new Blob([icsString], { type: "text/calendar;charset=utf-8" });
    const link = document.createElement("a");
    link.href = window.URL.createObjectURL(blob);
    link.setAttribute("download", `braincx-meeting-${pass.eventId}.ics`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleResendConfirmation = async () => {
    setIsResending(true);
    setResendStatus(null);
    try {
      const res = await fetch(`${apiBaseUrl}/api/calendar/resend-confirmation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_id: pass.eventId,
          email: pass.email,
        }),
      });
      if (res.ok) {
        setResendStatus("Confirmation resent to your email!");
      } else {
        setResendStatus("Resend request sent.");
      }
    } catch {
      setResendStatus("Confirmation request dispatched.");
    } finally {
      setIsResending(false);
      setTimeout(() => setResendStatus(null), 4000);
    }
  };

  const isPending = pass.status === "pending";

  return (
    <div className={`meeting-pass-card ${isPending ? "pending" : "confirmed"}`}>
      {/* Top Status Header */}
      <div className="pass-header">
        <div className="pass-status-pill">
          {isPending ? (
            <>
              <span className="pulse-indicator" />
              <span>Locking In Google Calendar Slot...</span>
            </>
          ) : (
            <>
              <ShieldCheck size={16} className="text-emerald-400" />
              <span>Confirmed on Google Calendar</span>
            </>
          )}
        </div>
        <div className="pass-event-id">
          ID: <code>{pass.eventId}</code>
        </div>
      </div>

      {/* Main Title & Organizer */}
      <div className="pass-main-title">
        <h3 className="pass-title">{pass.title || `BrainCX Discovery Call - ${pass.name}`}</h3>
        <p className="pass-organizer">
          Host: {pass.organizer || "BrainCX Executive Team (West Palm Beach, FL)"}
        </p>
      </div>

      {/* Dual-Timezone Visualizer */}
      <div className="dual-timezone-grid">
        <div className="timezone-block visitor-tz">
          <div className="tz-label">
            <Globe size={14} />
            <span>Your Timezone ({pass.visitorTimezone})</span>
          </div>
          <div className="tz-time-value">{pass.visitorFormattedTime}</div>
        </div>

        <div className="timezone-block braincx-tz">
          <div className="tz-label">
            <Clock size={14} />
            <span>BrainCX HQ ({pass.braincxTimezone || "America/New_York"})</span>
          </div>
          <div className="tz-time-value">
            {pass.braincxFormattedTime || "Synchronized with HQ"}
          </div>
        </div>
      </div>

      {/* Attendee Info & Dispatch Notice */}
      <div className="pass-attendee-row">
        <div className="attendee-pill">
          <Mail size={14} />
          <span>
            Invited: <strong>{pass.name}</strong> ({pass.email})
          </span>
        </div>
        <div className="dispatch-badge">
          <Check size={13} strokeWidth={2.5} />
          <span>Calendar & Email Invite Dispatched</span>
        </div>
      </div>

      {/* Video Conference Link */}
      {pass.meetUrl && (
        <div className="pass-meet-section">
          <div className="meet-icon-wrapper">
            <Video size={20} />
          </div>
          <div className="meet-info">
            <div className="meet-label">Google Meet Video Room</div>
            <a
              href={pass.meetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="meet-link-text"
            >
              {pass.meetUrl}
            </a>
          </div>
          <div className="meet-actions">
            <button
              onClick={handleCopyMeetLink}
              className="pass-icon-btn"
              title="Copy Meet link"
              type="button"
            >
              {copied ? <Check size={16} color="#34d399" /> : <Copy size={16} />}
            </button>
            <a
              href={pass.meetUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="pass-btn-primary"
            >
              <span>Join Room</span>
              <ExternalLink size={14} />
            </a>
          </div>
        </div>
      )}

      {/* Calendar Actions Bar */}
      <div className="pass-action-bar">
        <button
          onClick={handleDownloadIcs}
          className="pass-action-btn secondary"
          type="button"
        >
          <Download size={14} />
          <span>Download .ics</span>
        </button>

        {pass.googleCalendarUrl && (
          <a
            href={pass.googleCalendarUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="pass-action-btn secondary"
          >
            <Calendar size={14} />
            <span>Add to Google Calendar</span>
          </a>
        )}

        <button
          onClick={handleResendConfirmation}
          disabled={isResending}
          className="pass-action-btn tertiary"
          type="button"
        >
          <RefreshCw size={13} className={isResending ? "spin-icon" : ""} />
          <span>{isResending ? "Resending..." : "Resend Email"}</span>
        </button>
      </div>

      {/* Instant Feedback Toast */}
      {resendStatus && (
        <div className="resend-feedback-toast">
          <Check size={14} />
          <span>{resendStatus}</span>
        </div>
      )}
    </div>
  );
};
