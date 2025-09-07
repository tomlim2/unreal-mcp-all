'use client';

import { Inter, Bodoni_Moda } from "next/font/google";
import ModalProvider from "./components/modal/ModalProvider";
import ToastProvider from "./components/toast/ToastProvider";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

const bodoniModa = Bodoni_Moda({
  variable: "--font-bodoni-moda",
  subsets: ["latin"],
  weight: ["400", "700"],
});

export default function RootLayout({
  children,
  params,
}: Readonly<{
  children: React.ReactNode;
  params?: Promise<any>;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${bodoniModa.variable}`} suppressHydrationWarning>
        <ToastProvider position="top-right" maxToasts={5}>
          <ModalProvider>
            {children}
          </ModalProvider>
        </ToastProvider>
      </body>
    </html>
  );
}
