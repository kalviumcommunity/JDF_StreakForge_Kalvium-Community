import path from 'node:path';
import { pathToFileURL } from 'node:url';
import type { Page } from '@playwright/test';

export const PROTO = pathToFileURL(path.resolve(__dirname, '../../docs/prototype/streakforge_prototype.html')).href;
export const PAGES = ['overview', 'kpis', 'insights', 'risk', 'activation', 'share'] as const;

/** Opens the prototype (hash routes) or the built site (real paths) in a given theme. */
export async function open(page: Page, who: 'proto' | 'site', route: string, theme: 'light' | 'dark') {
  await page.addInitScript((t) => { try { localStorage.setItem('sf-theme', t); } catch { /* ignore */ } }, theme);
  const url = who === 'proto' ? `${PROTO}#${route}` : `/${route}/`;
  await page.goto(url);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(500);
}

export async function settle(page: Page) {
  await page.evaluate(async () => { await document.fonts.ready; window.scrollTo(0, 0); });
  await page.waitForTimeout(600);
}
