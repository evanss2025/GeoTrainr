import type { Metadata } from "next";
import "./globals.css";
import localFont from 'next/font/local';
import { Albert_Sans } from "next/font/google";

export const metadata: Metadata = {
  title: "GeoTrainr",
  description: "GeoTrainr",
};

const albert_sans = Albert_Sans({
  variable: "--font-albert-sans",
  subsets: ["latin"],
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${albert_sans.className} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
