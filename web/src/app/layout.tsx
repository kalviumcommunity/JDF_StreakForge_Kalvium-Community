import type { Metadata, Viewport } from 'next';
import '@/styles/fonts.css';
import '@/styles/tokens.css';
import '@/styles/globals.css';
import { loadData } from '@/lib/data';
import { AppProvider } from '@/lib/app';
import { Main, ProvenanceStrip, SkipLink, Toast, TopBar } from '@/components/Shell';

const description = 'An interactive read of 16,956 gym members: where they join, where they vanish, and the twelve worth calling this week. Synthetic data, fully disclosed.';
export const metadata: Metadata = {
  title: 'StreakForge — The First Seven Days',
  description,
  icons: { icon: '/favicon.svg' },
  openGraph: { title: 'StreakForge — The First Seven Days', description: '81 in 100 members never show up in week one. Explore the funnel, the as-of date trap and the 12 members worth a call.', type: 'website' },
};
export const viewport: Viewport = { width: 'device-width', initialScale: 1, themeColor: '#F4F1EA' };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const data = loadData();
  return (
    <html lang="en" data-theme="light" suppressHydrationWarning>
      <head>
        <script src="/theme-init.js" />
        <link rel="preload" href="/fonts/big-shoulders-display-800-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/hanken-grotesk-400-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        <link rel="preload" href="/fonts/ibm-plex-mono-500-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
      </head>
      <body>
        <AppProvider data={data}>
          <SkipLink />
          <TopBar />
          <ProvenanceStrip />
          <Main>{children}</Main>
          <Toast />
          <div id="printReport" aria-hidden="true" />
        </AppProvider>
      </body>
    </html>
  );
}
