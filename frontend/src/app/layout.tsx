import '@mantine/core/styles.css';
import type { Metadata } from 'next';
import { ColorSchemeScript, MantineProvider } from '@mantine/core';

export const metadata: Metadata = {
  title: 'Auction Analysis Agent',
  description: 'An automated agent to find undervalued auctions.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>{children}</MantineProvider>
      </body>
    </html>
  );
}
