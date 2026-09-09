"use client";

import React, { useEffect, useRef } from "react";
import { MessageSquare, CalendarCheck, Wrench } from "lucide-react";
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

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({
  messages,
  latestBooking,
  meetingPass,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

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
          {messages.length} {messages.length === 1 ? "turn" : "turns"}
        </span>
      </div>

      <div className="transcript-body" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="transcript-empty">
            <MessageSquare size={36} strokeWidth={1.5} color="#475569" />
            <p>Ready to converse. Start the call to speak with the BrainCX voice representative.</p>
          </div>
        ) : (
          messages.map((msg) => {
            if (msg.role === "tool") {
              return (
                <div key={msg.id} className="tool-callout">
                  <Wrench size={14} />
                  <span>Calendar Tool: {msg.toolName || "Executing"}</span>
                </div>
              );
            }

            const isAssistant = msg.role === "assistant";

            return (
              <div
                key={msg.id}
                className={`chat-bubble ${isAssistant ? "assistant" : "user"}`}
              >
                <span className={`bubble-sender ${isAssistant ? "assistant" : ""}`}>
                  {isAssistant ? "BrainCX Representative" : "You"}
                </span>
                <div className="bubble-text">{msg.text}</div>
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

