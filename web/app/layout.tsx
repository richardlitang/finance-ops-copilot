import type { Metadata } from "next";

import "./styles.css";

export const metadata: Metadata = {
  title: "Finance Ops Copilot",
  description: "Receipt-first reconciliation console",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
