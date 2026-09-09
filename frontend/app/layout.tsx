import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BrainCX AI Voice Agent | The AI CX Operator",
  description:
    "Official BrainCX interactive web voice agent. Explore AI CX operations for high-consequence verticals and schedule a live meeting via Google Calendar.",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
