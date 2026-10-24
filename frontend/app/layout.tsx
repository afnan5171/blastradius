import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "BlastRadius — Know your exposure",
  description: "Understand how your accounts connect. Protect what matters.",
};
export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
