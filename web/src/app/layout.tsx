import type { Metadata } from "next";
import { Hanken_Grotesk } from "next/font/google";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";

import { DotCanvas } from "@/components/dot-canvas";
import "./globals.css";

const hanken = Hanken_Grotesk({
  subsets: ["latin"],
  variable: "--font-hanken",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "S.A.R.A.L. - System Online",
  description:
    "Secure, transparent, and direct access to essential institutional services and eligibility frameworks.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} className={`light ${hanken.variable}`}>
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="relative z-0 min-h-screen font-sans text-on-background antialiased">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <div className="light-glow" aria-hidden />
          <DotCanvas />
          <div className="relative z-10">{children}</div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
