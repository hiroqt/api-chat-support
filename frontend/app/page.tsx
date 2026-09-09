"use client";

import React, { useState } from "react";
import { BrandHeader } from "@/components/BrandHeader";
import { VoiceWidget } from "@/components/VoiceWidget";
import { TranscriptPanel, MessageTurn, BookingDetails } from "@/components/TranscriptPanel";

export default function HomePage() {
  const [callStatus, setCallStatus] = useState<
    "idle" | "connecting" | "connected" | "speaking" | "listening" | "ended" | "error"
  >("idle");

  const [messages, setMessages] = useState<MessageTurn[]>([]);
  const [latestBooking, setLatestBooking] = useState<BookingDetails | null>(null);

  const handleNewMessage = (msg: MessageTurn) => {
    setMessages((prev) => [...prev, msg]);
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
              onBookingConfirmed={handleBookingConfirmed}
            />

            <TranscriptPanel
              messages={messages}
              latestBooking={latestBooking}
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
