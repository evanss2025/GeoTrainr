import type { Metadata } from "next";
import "./globals.css";
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
      <link
        rel="icon"
        href="/icon?<generated>"
        type="image/<generated>"
        sizes="<generated>"
      />
      <body
        className={`${albert_sans.className} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
