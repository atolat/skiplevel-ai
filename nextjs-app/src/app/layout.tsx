import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext'

export const metadata: Metadata = {
  title: "Emreq Terminal | AI Engineering Manager",
  description: "Terminal-style interface for your AI Engineering Manager",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-gray-900 text-gray-100">
        <AuthProvider>
          <div className="min-h-screen flex flex-col">
            {/* Terminal-style header */}
            <header className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
              <div className="flex space-x-2">
                <div className="w-3 h-3 rounded-full bg-red-500"></div>
                <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
              </div>
              <div className="text-sm font-mono">
                emreq@terminal:~$
              </div>
              <div className="w-16"></div> {/* Spacer for balance */}
            </header>
            
            {/* Main content */}
            <main className="flex-1 overflow-hidden">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
