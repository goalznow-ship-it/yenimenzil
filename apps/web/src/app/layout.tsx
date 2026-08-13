import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { TooltipProvider } from "@yenimenzil/ui";
import { AuthProvider } from "@/components/auth/auth-provider";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { MobileNav } from "@/components/layout/mobile-nav";
import { CookieConsent } from "@/components/cookie-consent";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
  display: "swap"
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
  display: "swap"
});

export const metadata: Metadata = {
  metadataBase: new URL("https://yenimenzil.az"),
  title: {
    default: "YeniMenzil.az — Yeni məkanını burada tap",
    template: "%s | YeniMenzil.az"
  },
  description:
    "Azərbaycan üzrə mənzil, villa, torpaq, obyekt və digər daşınmaz əmlak elanlarını rahat şəkildə kəşf et.",
  keywords: [
    "daşınmaz əmlak",
    "mənzil",
    "kirayə",
    "villa",
    "torpaq",
    "Bakı",
    "yenimenzil"
  ],
  openGraph: {
    siteName: "YeniMenzil.az",
    title: "YeniMenzil.az — Yeni məkanını burada tap",
    description:
      "Azərbaycan üzrə mənzil, villa, torpaq, obyekt və digər daşınmaz əmlak elanlarını rahat şəkildə kəşf et.",
    locale: "az_AZ",
    type: "website"
  },
  robots: {
    index: true,
    follow: true
  }
};

export const viewport: Viewport = {
  themeColor: "#F7F8F6",
  width: "device-width",
  initialScale: 1
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="az" className={`${geistSans.variable} ${geistMono.variable}`}>
      <body className="min-h-dvh font-sans">
        <TooltipProvider delayDuration={300}>
          <AuthProvider>
            <div className="flex min-h-dvh flex-col">
              <Header />
              <main className="flex-1 pb-20 md:pb-0">{children}</main>
              <Footer />
              <MobileNav />
              <CookieConsent />
            </div>
          </AuthProvider>
        </TooltipProvider>
      </body>
    </html>
  );
}
