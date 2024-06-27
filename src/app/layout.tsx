import "~/styles/globals.css";

import { GeistSans } from "geist/font/sans";

import { TRPCReactProvider } from "~/trpc/react";
import { Manrope } from 'next/font/google'
import { cn } from '~/lib/utils'

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
        <TRPCReactProvider>{children}</TRPCReactProvider>
      </body>
    </html>
  );
}
