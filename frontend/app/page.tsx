"use client";

import React, { useState } from "react";
import { BrandHeader } from "@/components/BrandHeader";
import { VoiceWidget } from "@/components/VoiceWidget";
import { TranscriptPanel, MessageTurn, BookingDetails } from "@/components/TranscriptPanel";
import { MeetingPassData } from "@/components/MeetingPassCard";

function cleanShatteredText(text: string): string {
  if (!text) return "";
  return text
    // Reassemble shattered URLs, e.g. "https://. meet.google.com/. abs. gfqs-nd. G." -> "https://meet.google.com/abs-gfqs-ndg"
    .replace(/https?:\/\/\s*\.?\s*/gi, "https://")
    .replace(/meet\.google\.com\/\s*\.?\s*/gi, "meet.google.com/")
    .replace(/(meet\.google\.com\/[a-z0-9-]+)\s*[\.-]\s*([a-z0-9-]+)/gi, "$1-$2")
    .replace(/(meet\.google\.com\/[a-z0-9-]+)\s*[\.-]\s*([a-z0-9]+)/gi, "$1-$2")
    .replace(/\s+\./g, ".")
    .replace(/\s+/g, " ")
    .trim();
}

export default function HomePage() {
  const [callStatus, setCallStatus] = useState<
    "idle" | "connecting" | "connected" | "speaking" | "listening" | "ended" | "error"
  >("idle");

  const [messages, setMessages] = useState<MessageTurn[]>([]);
  const [latestBooking, setLatestBooking] = useState<BookingDetails | null>(null);
  const [meetingPass, setMeetingPass] = useState<MeetingPassData | null>(null);

  const handleNewMessage = (msg: MessageTurn) => {
    const cleanedText = cleanShatteredText(msg.text);
    if (!cleanedText) return;

    setMessages((prev) => {
      if (prev.length === 0) {
        return [{ ...msg, text: cleanedText }];
      }

      const lastMsg = prev[prev.length - 1];

      // If the incoming message is from the SAME speaker (e.g. consecutive assistant chunks),
      // merge them into a single cohesive conversational turn instead of shattering into multiple bubbles!
      if (lastMsg.role === msg.role) {
        const prevText = lastMsg.text.trim();
        if (prevText.endsWith(cleanedText)) {
          return prev;
        }
        if (cleanedText.startsWith(prevText)) {
          return [...prev.slice(0, -1), { ...lastMsg, text: cleanedText }];
        }

        const separator =
          prevText.endsWith(".") ||
          prevText.endsWith("?") ||
          prevText.endsWith("!") ||
          prevText.endsWith(":")
            ? " "
            : " ";
        const merged = cleanShatteredText(`${prevText}${separator}${cleanedText}`);
        const updatedLast: MessageTurn = {
          ...lastMsg,
          text: merged,
          timestamp: msg.timestamp || lastMsg.timestamp,
        };
        return [...prev.slice(0, -1), updatedLast];
      }

      // Role changed -> start new conversational turn bubble
      return [...prev, { ...msg, text: cleanedText }];
    });
  };

  const handleBookingConfirmed = (booking: BookingDetails) => {
    setLatestBooking(booking);
  };

  return (
    <>
      <BrandHeader status={callStatus} />

      <main className="main-content">
        <div className="container">
          <div className="grid-layout">
            <VoiceWidget
              status={callStatus}
              setStatus={setCallStatus}
              onNewMessage={handleNewMessage}
              onMeetingPassUpdated={setMeetingPass}
              onBookingConfirmed={handleBookingConfirmed}
            />

            <TranscriptPanel
              messages={messages}
              latestBooking={latestBooking}
              meetingPass={meetingPass}
            />
          </div>
        </div>
      </main>

      <footer className="footer">
        <div className="container footer-inner">
          <div>
            © {new Date().getFullYear()} BrainCX Inc. West Palm Beach, Florida. All rights reserved.
          </div>
          <div>
            Patent-Pending • 99.9% Uptime SLA • SOC 2 Type II & HIPAA Compliant
          </div>
        </div>
      </footer>
    </>
  );
}
