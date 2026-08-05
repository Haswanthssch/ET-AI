import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ETAI — Data Centre EPC Intelligence",
  description:
    "AI intelligence platform for hyperscale data centre EPC project delivery.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
