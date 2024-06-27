import "~/styles/globals.css";

import { GeistSans } from "geist/font/sans";

import { TRPCReactProvider } from "~/trpc/react";
import { Manrope } from 'next/font/google'
import { cn } from '~/lib/utils'
import Sidebar from "~/components/Sidebar";
import Navigation from "~/components/Navigation";

const fontHeading = Manrope({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-heading',
})

const fontBody = Manrope({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
})

export const metadata = {
  title: "Finka",
  description: "Finance Management",
  icons: [{ rel: "icon", url: "/favicon.svg" }],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={`${GeistSans.variable}`}>
      <body
        className={cn(
          'antialiased',
          fontHeading.variable,
          fontBody.variable
        )}
      >
        <TRPCReactProvider>
          <div className="grid min-h-screen w-full grid-cols-1 bg-muted/40 lg:grid-cols-[280px_1fr]">
            <div className="hidden border-r bg-muted/40 lg:block">
              <Sidebar />
            </div>
            <div className="flex flex-col">
              <Navigation />
              {children}
            </div>
          </div>
        </TRPCReactProvider>
      </body>
    </html>
  );
}
