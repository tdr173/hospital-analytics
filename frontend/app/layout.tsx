import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";
import EmotionRegistry from "./EmotionRegistry";

export const metadata: Metadata = {
  title: "HospitAI - Hospital Analytics Dashboard",
  description: "A comprehensive platform for hospital analytics",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <EmotionRegistry>
          <Providers>{children}</Providers>
        </EmotionRegistry>
      </body>
    </html>
  );
}
