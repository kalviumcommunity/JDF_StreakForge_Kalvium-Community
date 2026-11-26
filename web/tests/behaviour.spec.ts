import { test, expect, type Page } from '@playwright/test';
import fs from 'node:fs';
import { PAGES } from './helpers';

const goto = async (page: Page, p: string) => { await page.goto(`/${p}/`); await page.waitForLoadState('networkidle'); };

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(String(e)));
  (page as unknown as { __errors: string[] }).__errors = errors;
});
test.afterEach(async ({ page }) => { expect((page as unknown as { __errors: string[] }).__errors, 'console errors').toEqual([]); });

test('root redirects; landing opens on chapter 05 with chapters in order', async ({ page }) => {
  await page.goto('/'); await page.waitForURL('**/overview/');
  const tabs = page.locator('.stage button');
  await expect(tabs).toHaveText(['01Everyone', '02The first seven days', '03Who is still here', '04Four kinds of member', '05Twelve to call']);
  await expect(page.locator('.stage button[aria-selected=true]')).toContainText('Twelve to call');
  await expect(page.locator('#hud')).toContainText('12');
  await expect(page.locator('h1')).toHaveCount(1);
});

test('chapters: click, arrow keys, day slider, replay, play', async ({ page }) => {
  await goto(page, 'overview');
  await page.locator('.stage button[data-i="1"]').click();
  await expect(page.locator('#storyH')).toContainText('lit up');
  await page.locator('#day').fill('3');
  await expect(page.locator('#hud')).toContainText('activated by day 3');
  await page.locator('.stage button[data-i="1"]').focus();
  await page.keyboard.press('ArrowRight');
  await expect(page.locator('.stage button[aria-selected=true]')).toContainText('Who is still here');
  await page.locator('#play').click();
  await expect(page.locator('#toast')).toHaveClass(/on/);
});

test('as-of toggle changes strip, field HUD and clocks together', async ({ page }) => {
  await goto(page, 'overview');
  await expect(page.locator('#provAsof')).toContainText('Pipeline as-of 2026-08-14');
  await page.locator('.stage button[data-i="2"]').click();
  await expect(page.locator('#hud')).toContainText('1,011');
  await page.locator('.prov [data-asof=data]').click();
  await expect(page.locator('#provAsof')).toContainText('Realistic as-of 2025-10-05');
  await expect(page.locator('#hud')).toContainText('2,711');
  await expect(page.locator('#main .radio[data-asof=data]')).toHaveAttribute('aria-checked', 'true');
  await expect(page.locator('#clockSvg')).toContainText('churn 84.0%');
});

test('KPI ledger: accordion, jump to twin, search empty state', async ({ page }) => {
  await goto(page, 'kpis');
  await expect(page.locator('.lrow')).toHaveCount(15);
  await page.locator('[data-k=kpi_01] .lhead').click();
  await expect(page.locator('[data-k=kpi_01] .lhead')).toHaveAttribute('aria-expanded', 'true');
  await page.locator('[data-jump=kpi_15]').click();
  await expect(page.locator('[data-k=kpi_15]')).toHaveClass(/open/);
  await expect(page.locator('.lrow.open')).toHaveCount(1);
  await page.locator('#kq').fill('zzzz');
  await expect(page.locator('.empty')).toContainText('No KPI matches');
  await page.locator('#kclear').click();
  await expect(page.locator('.lrow')).toHaveCount(15);
});

test('Insights: audience chips and dossier evidence link', async ({ page }) => {
  await goto(page, 'insights');
  await expect(page.locator('.dossier')).toHaveCount(5);
  await page.locator('[data-aud=Finance]').click();
  await expect(page.locator('.dossier')).toHaveCount(1);
  await page.locator('[data-aud=All]').click();
  await page.locator('.dossier[data-i="INS-02"] .dh').click();
  await page.locator('.dossier[data-i="INS-02"] a').click();
  await page.waitForURL('**/activation/');
});

test('Risk: bubble selection, sort, mark contacted, search', async ({ page }) => {
  await goto(page, 'risk');
  await expect(page.locator('.bub')).toHaveCount(40);
  await page.locator('#bHigh').click();
  await expect(page.locator('.bub.sel')).toHaveCount(1);
  await expect(page.locator('#bcard h3')).toContainText('BR-');
  await page.locator('#bClear').click();
  await expect(page.locator('#bcard h3')).toHaveText('Pick a bubble');
  await page.locator('.bub').first().focus(); await page.keyboard.press('Enter');
  await expect(page.locator('.bub.sel')).toHaveCount(1);
  await expect(page.locator('#rtbl tbody tr')).toHaveCount(12);
  await page.locator('[data-sort=events]').click();
  await expect(page.locator('th[aria-sort=descending]')).toContainText('Events');
  await page.locator('[data-done]').first().click();
  await expect(page.locator('#rcount')).toContainText('1 contacted');
  await page.locator('#rq').fill('MBR-000273');
  await expect(page.locator('#rtbl tbody tr')).toHaveCount(1);
  await page.locator('#rq').fill('nomatch');
  await expect(page.locator('#rclear')).toBeVisible();
});

test('Activation: cohort ranges, arrow-key read-out, segment tabs', async ({ page }) => {
  await goto(page, 'activation');
  await page.locator('[data-rng="12"]').click();
  await page.locator('#cchart svg').focus(); await page.keyboard.press('ArrowRight');
  await expect(page.locator('#ctip')).toContainText('members');
  await page.locator('[data-dim=city_tier]').click();
  await expect(page.locator('.srow')).toHaveCount(3);
  await expect(page.locator('#vcard')).toContainText('Weak');
});

test('Share: markdown and zip downloads; email disabled', async ({ page }) => {
  await goto(page, 'share');
  const [md] = await Promise.all([page.waitForEvent('download'), page.locator('#xMd').click()]);
  const text = fs.readFileSync((await md.path())!, 'utf8');
  expect(text).toContain('# StreakForge brief'); expect(text).toContain('MBR-000763');
  const [z] = await Promise.all([page.waitForEvent('download'), page.locator('#xZip').click()]);
  const buf = fs.readFileSync((await z.path())!);
  expect(buf.readUInt32LE(0)).toBe(0x04034b50);
  expect(buf.readUInt16LE(buf.length - 22 + 10)).toBe(6); // six files
  await expect(page.getByRole('button', { name: 'Send by email' })).toBeDisabled();
  await expect(page.locator('.sc').nth(3)).toContainText('Under development');
  await page.locator('.prov [data-asof=data]').click();
  await expect(page.locator('#pv')).toContainText('84.0% (data-realistic');
});

test('404 page', async ({ page }) => {
  const r = await page.goto('/definitely-missing/'); expect(r?.status()).toBe(404);
  (page as unknown as { __errors: string[] }).__errors.length = 0; // the browser logs the deliberate 404 response itself
  await expect(page.locator('.nf .num')).toHaveText('404');
  await expect(page.locator('footer')).toHaveCount(0);
});

test('theme toggle persists; no filter UI anywhere', async ({ page }) => {
  await goto(page, 'overview');
  await page.locator('#themeBtn').click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  await page.reload(); await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');
  for (const p of PAGES) { await goto(page, p); await expect(page.getByRole('button', { name: /^filters/i })).toHaveCount(0); }
});

test('mobile 390px: no horizontal scroll on any page', async ({ browser }) => {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } }); const page = await ctx.newPage();
  for (const p of PAGES) { await goto(page, p); const o = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth); expect(o, p).toBeLessThanOrEqual(0); }
  await ctx.close();
});
