"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Mic, MicOff, Phone, PhoneOff, Volume2, ShieldCheck, CheckCircle2 } from "lucide-react";
import { getVapiClient } from "@/lib/vapi";
import { MessageTurn, BookingDetails } from "./TranscriptPanel";

interface VoiceWidgetProps {
  status: "idle" | "connecting" | "connected" | "speaking" | "listening" | "ended" | "error";
  setStatus: React.Dispatch<
    React.SetStateAction<"idle" | "connecting" | "connected" | "speaking" | "listening" | "ended" | "error">
  >;
  onNewMessage: (msg: MessageTurn) => void;
  onBookingConfirmed: (booking: BookingDetails) => void;
}

export const VoiceWidget: React.FC<VoiceWidgetProps> = ({
  status,
  setStatus,
  onNewMessage,
  onBookingConfirmed,
}) => {
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isInCall =
    status === "connected" || status === "speaking" || status === "listening";

  const handleStartCall = useCallback(async () => {
    setErrorMessage(null);
    setStatus("connecting");

    try {
      const publicKey = process.env.NEXT_PUBLIC_VAPI_PUBLIC_KEY;
      const assistantId = process.env.NEXT_PUBLIC_VAPI_ASSISTANT_ID;

      if (!publicKey || publicKey.includes("mock") || publicKey.includes("copied") || publicKey.includes("your-")) {
        throw new Error(
          "Please paste your real Vapi Public Key into frontend/.env.local (found in Vapi Dashboard > API Keys > Public API Key)."
        );
      }

      if (!assistantId || assistantId.includes("mock")) {
        throw new Error(
          "Please set your real NEXT_PUBLIC_VAPI_ASSISTANT_ID in frontend/.env.local."
        );
      }

      // Pre-flight check: probe browser microphone permission
      if (typeof navigator !== "undefined" && navigator.mediaDevices?.getUserMedia) {
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          stream.getTracks().forEach((track) => track.stop());
        } catch (micErr: any) {
          if (micErr.name === "NotAllowedError" || micErr.name === "PermissionDeniedError") {
            throw new Error(
              "Microphone access was denied. Please allow microphone permissions in your browser to speak with BrainCX."
            );
          }
        }
      }

      const vapi = getVapiClient();
      console.log(`Initiating Vapi call with Assistant ID: ${assistantId}`);
      await vapi.start(assistantId);
    } catch (err: any) {
      console.error("Failed to start voice call:", err);
      setStatus("error");
      const msg = err?.error?.message?.message || err?.message || "Vapi authorization error.";
      if (msg.includes("private key instead of the public key") || msg.includes("Invalid Key")) {
        setErrorMessage(
          "Vapi Error (401): You pasted the Private Key instead of the Public Key. In Vapi Dashboard > API Keys, copy the top 'Public API Key' and paste it into frontend/.env.local."
        );
      } else {
        setErrorMessage(msg);
      }
    }
  }, [setStatus]);


  const handleEndCall = useCallback(() => {
    try {
      const vapi = getVapiClient();
      vapi.stop();
    } catch (err) {
      console.warn("Error stopping vapi call:", err);
    }
    setStatus("ended");
  }, [setStatus]);

  const handleToggleMute = useCallback(() => {
    try {
      const vapi = getVapiClient();
      const nextMuted = !isMuted;
      vapi.setMuted(nextMuted);
      setIsMuted(nextMuted);
    } catch (err) {
      console.warn("Could not toggle mute:", err);
      setIsMuted(!isMuted);
    }
  }, [isMuted]);

  // Vapi event listener bindings
  useEffect(() => {
    let vapi: any = null;
    try {
      vapi = getVapiClient();
    } catch (e) {
      return;
    }

    const onCallStart = () => {
      setStatus("connected");
    };

    const onCallEnd = () => {
      setStatus("ended");
      setIsMuted(false);
    };

    const onSpeechStart = () => {
      setStatus("speaking");
    };

    const onSpeechEnd = () => {
      setStatus("listening");
    };

    const onError = (e: any) => {
      console.error("Vapi Error:", e);
      setStatus("error");
      setErrorMessage(e?.message || "An audio stream error occurred.");
    };

    const onMessage = (message: any) => {
      if (message.type === "transcript" && message.transcriptType === "final") {
        onNewMessage({
          id: `${Date.now()}-${Math.random()}`,
          role: message.role === "assistant" ? "assistant" : "user",
          text: message.transcript,
          timestamp: new Date().toLocaleTimeString(),
        });
      }

      if (message.type === "function-call") {
        const fnName = message.functionCall?.name;
        onNewMessage({
          id: `${Date.now()}-tool`,
          role: "tool",
          text: `Executing tool: ${fnName}`,
          toolName: fnName,
          timestamp: new Date().toLocaleTimeString(),
        });

        if (fnName === "book_meeting") {
          const args = message.functionCall?.parameters || {};
          onBookingConfirmed({
            eventId: "pending-verification",
            name: args.name || "Visitor",
            date: args.start?.split("T")[0] || "Scheduled Date",
            time: args.start?.split("T")[1] || "Scheduled Time",
            timezone: args.timezone || "Local Time",
          });
        }
      }
    };

    vapi.on("call-start", onCallStart);
    vapi.on("call-end", onCallEnd);
    vapi.on("speech-start", onSpeechStart);
    vapi.on("speech-end", onSpeechEnd);
    vapi.on("error", onError);
    vapi.on("message", onMessage);

    return () => {
      vapi.off("call-start", onCallStart);
      vapi.off("call-end", onCallEnd);
      vapi.off("speech-start", onSpeechStart);
      vapi.off("speech-end", onSpeechEnd);
      vapi.off("error", onError);
      vapi.off("message", onMessage);
    };
  }, [onBookingConfirmed, onNewMessage, setStatus]);

  // Determine label and core styling based on status
  let statusText = "Ready to speak with BrainCX";
  let subText = "Click 'Start Voice Call' to begin a live conversation";
  let orbCoreClass = "";
  let orbRingClass = "";

  if (status === "connecting") {
    statusText = "Establishing Voice Stream...";
    subText = "Connecting to BrainCX AI representative";
    orbCoreClass = "connected";
  } else if (status === "speaking") {
    statusText = "BrainCX is speaking";
    subText = "Feel free to speak up or interrupt at any time";
    orbCoreClass = "speaking";
    orbRingClass = "speaking";
  } else if (status === "listening") {
    statusText = "Listening to you...";
    subText = "Speak naturally into your microphone";
    orbCoreClass = "listening";
    orbRingClass = "listening";
  } else if (status === "ended") {
    statusText = "Call Finished";
    subText = "Thank you for speaking with BrainCX";
  } else if (status === "error") {
    statusText = "Connection Notice";
    subText = errorMessage || "Voice stream temporarily disconnected";
  }

  return (
    <div className="console-card">
      <div className="console-header">
        <h1 className="console-title">Interactive Voice Representative</h1>
        <p className="console-subtitle">
          Real-time voice interface powered by BrainCX and synchronized with live Google Calendar availability.
        </p>
      </div>

      <div className="visualizer-stage">
        <div className="orb-wrapper">
          <div className={`orb-ring ${orbRingClass}`} />
          <div className={`orb-core ${orbCoreClass}`}>
            {status === "speaking" ? (
              <Volume2 size={32} />
            ) : status === "listening" ? (
              <Mic size={32} />
            ) : (
              <Phone size={32} />
            )}
          </div>
        </div>

        <div className="visualizer-status-text">{statusText}</div>
        <div className="visualizer-subtext">{subText}</div>
      </div>

      <div className="call-actions">
        {!isInCall ? (
          <button
            id="start-voice-call-btn"
            className="btn-primary"
            onClick={handleStartCall}
            disabled={status === "connecting"}
          >
            <Phone size={18} />
            <span>{status === "connecting" ? "Connecting..." : "Start Voice Call"}</span>
          </button>
        ) : (
          <>
            <button
              id="end-voice-call-btn"
              className="btn-danger"
              onClick={handleEndCall}
            >
              <PhoneOff size={18} />
              <span>End Call</span>
            </button>

            <button
              id="toggle-mute-btn"
              className={`btn-secondary ${isMuted ? "active" : ""}`}
              onClick={handleToggleMute}
              title={isMuted ? "Unmute microphone" : "Mute microphone"}
            >
              {isMuted ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
          </>
        )}
      </div>

      <div className="info-box">
        <div className="info-box-title">BrainCX Representation Standard</div>
        <ul className="info-box-list">
          <li>The AI CX Operator for high consequence verticals</li>
          <li>Gives existing agents capacity — never replaces human workforce</li>
          <li>Live Google Calendar synchronization for real meeting booking</li>
          <li>Outcome-based commercial model with enterprise HIPAA & SOC 2</li>
        </ul>
      </div>
    </div>
  );
};
