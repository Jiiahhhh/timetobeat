import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TimeToBeat | Find Your Next Game Tonight",
  description:
    "Stop staring at your backlog. Tell us how much time you have tonight and we'll tell you exactly which game to play. Free, no login required.",

  // Canonical URL
  metadataBase: new URL("https://timetobeat.app"),
  alternates: {
    canonical: "/",
  },

  // Open Graph — for Discord, Facebook, WhatsApp previews
  openGraph: {
    title: "TimeToBeat | Find Your Next Game Tonight",
    description:
      "Stop staring at your backlog. Tell us how much time you have and we'll tell you exactly which game to play.",
    url: "https://timetobeat.app",
    siteName: "TimeToBeat",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "TimeToBeat — Find your next game based on your available time",
      },
    ],
    locale: "en_US",
    type: "website",
  },

  // Twitter / X Card
  twitter: {
    card: "summary_large_image",
    title: "TimeToBeat | Find Your Next Game Tonight",
    description:
      "Stop staring at your backlog. Tell us how much time you have and we'll tell you exactly which game to play.",
    images: ["/og-image.png"],
  },

  // Additional SEO
  keywords: [
    "game recommendation",
    "backlog",
    "how long to beat",
    "steam games",
    "game picker",
    "time to beat",
    "gaming backlog",
    "what game should i play",
  ],
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <script
          defer
          src="https://cloud.umami.is/script.js"
          data-website-id="84463842-52eb-4da5-b148-01000a384eb4"
        ></script>
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
