import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"

const inter = Inter({
  subsets: ["latin"],
  // Load all brand-specified weights in one request
  weight: ["300", "400", "700", "900"],
  display: "swap",
})

export const metadata: Metadata = {
  title: "CoE Wiki",
  description: "Leapfrog Centre of Excellence knowledge base",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.className} h-full antialiased`}>
      <body className="min-h-full bg-brand-white text-brand-abyss font-sans">{children}</body>
    </html>
  )
}
