import type { Metadata, Viewport } from "next";
import "./globals.css";

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  title: "BrainCX AI Voice Agent | The AI CX Operator",
  description:
    "Official BrainCX interactive web voice agent. Explore AI CX operations for high-consequence verticals and schedule a live meeting via Google Calendar.",
  keywords: ["BrainCX", "AI CX Operator", "Voice AI", "Contact Center Automation", "Customer Experience"],
  authors: [{ name: "BrainCX Team" }],
  openGraph: {
    title: "BrainCX AI Voice Agent | The AI CX Operator",
    description: "Experience conversational AI for high-consequence verticals. Book live meetings seamlessly with synchronized Google Calendar availability.",
    url: "https://braincx.ai",
    siteName: "BrainCX",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "BrainCX AI Voice Agent | The AI CX Operator",
    description: "The AI CX Operator for high consequence verticals. Gives existing agents more capacity. It does not replace them.",
  },
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
