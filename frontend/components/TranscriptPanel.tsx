"use client";

import React, { useEffect, useRef } from "react";
import { MessageSquare, CalendarCheck } from "lucide-react";
import { MeetingPassCard, MeetingPassData } from "./MeetingPassCard";

export interface MessageTurn {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  text: string;
  toolName?: string;
  timestamp: string;
}

export interface BookingDetails {
  eventId: string;
  name: string;
  date: string;
  time: string;
  timezone: string;
}

interface TranscriptPanelProps {
  messages: MessageTurn[];
  latestBooking?: BookingDetails | null;
  meetingPass?: MeetingPassData | null;
}

function renderMessageText(text: string) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  return parts.map((part, i) => {
    if (part.match(urlRegex)) {
      return (
        <a
          key={i}
          href={part}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: "#60a5fa", textDecoration: "underline", wordBreak: "break-all" }}
        >
          {part}
        </a>
      );
    }
    return part;
  });
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  messages,
  latestBooking,
  meetingPass,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Show only natural conversational turns (filter out any internal tool messages)
  const conversationalMessages = messages.filter(
    (msg) => msg.role === "assistant" || msg.role === "user"
  );

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, latestBooking, meetingPass]);

  return (
    <div className="transcript-card">
      <div className="transcript-header">
        <span className="transcript-title">Live Conversation Stream</span>
        <span className="transcript-badge">
          {conversationalMessages.length} {conversationalMessages.length === 1 ? "turn" : "turns"}
        </span>
      </div>

      <div className="transcript-body" ref={scrollRef}>
        {conversationalMessages.length === 0 ? (
          <div className="transcript-empty">
            <MessageSquare size={36} strokeWidth={1.5} color="#475569" />
            <p>Ready to converse. Start the call to speak with the BrainCX voice representative.</p>
          </div>
        ) : (
          conversationalMessages.map((msg) => {
            const isAssistant = msg.role === "assistant";

            return (
              <div
                key={msg.id}
                className={`chat-bubble ${isAssistant ? "assistant" : "user"}`}
              >
                <span className={`bubble-sender ${isAssistant ? "assistant" : ""}`}>
                  {isAssistant ? "BrainCX Representative" : "You"}
                </span>
                <div className="bubble-text">{renderMessageText(msg.text)}</div>
              </div>
            );
          })
        )}

        {/* Priority: Interactive Meeting Pass Card */}
        {meetingPass && <MeetingPassCard pass={meetingPass} />}

        {/* Fallback Legacy Booking Banner if meetingPass not set */}
        {!meetingPass && latestBooking && (
          <div className="booking-banner">
            <div className="booking-banner-title">
              <CalendarCheck size={18} />
              <span>Meeting Confirmed on Google Calendar</span>
            </div>
            <div className="booking-banner-desc">
              Booked for <strong>{latestBooking.name}</strong> • Event ID: <code>{latestBooking.eventId}</code>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


