import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Meiyume Multimodal RAG Agent",
  description: "A focused document and image RAG assistant for material knowledge."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
