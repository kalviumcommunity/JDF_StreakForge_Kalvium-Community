/* Visual regression: the built site must match the prototype (the spec). Run `npm run build` first.
   Reduced motion is emulated on both sides so animations settle instantly and deterministically. */
import { test, expect } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
import { PNG } from 'pngjs';
import pixelmatch from 'pixelmatch';
import { PAGES, open, settle } from './helpers';

const SIZES = { desktop: { width: 1360, height: 860 }, mobile: { width: 390, height: 844 } };
const TOLERANCE = 0.01; // 1% of pixels may differ
const REF = path.resolve(__dirname, 'reference');
const OUT = path.resolve(__dirname, '.tmp');
fs.mkdirSync(REF, { recursive: true }); fs.mkdirSync(OUT, { recursive: true });

const shots: { name: string; route: string; chapter?: number }[] = [
  ...PAGES.filter((p) => p !== 'overview').map((p) => ({ name: p, route: p })),
  ...[0, 1, 2, 3, 4].map((c) => ({ name: `overview-ch${c + 1}`, route: 'overview', chapter: c })),
  { name: '404', route: 'not-a-page' },
];

for (const theme of ['light', 'dark'] as const) {
  for (const [sizeName, size] of Object.entries(SIZES)) {
    for (const s of shots) {
      test(`${s.name} · ${sizeName} · ${theme}`, async ({ browser }) => {
        const shoot = async (who: 'proto' | 'site') => {
          const ctx = await browser.newContext({ viewport: size, reducedMotion: 'reduce' });
          const page = await ctx.newPage();
          await open(page, who, s.route, theme);
          if (s.chapter !== undefined) { await page.locator(`.stage button[data-i="${s.chapter}"]`).click(); await page.waitForTimeout(400); }
          await page.addStyleTag({ content: 'footer{display:none!important}' + (s.route === 'overview' ? '.field-wrap{visibility:hidden!important}' : '') }); // the reference footer is not part of the site; the Field now sits in the page column (intentional change), so it is masked here
          await settle(page);
          // Risk page: the at-risk table intentionally differs (real rows replace the prototype's two samples), so compare the branch section only.
          const buf = s.name === 'risk' ? await page.locator('#branches').screenshot() : await page.screenshot({ fullPage: true, animations: 'disabled' });
          await ctx.close();
          return buf;
        };
        const ref = await shoot('proto');
        fs.writeFileSync(path.join(REF, `${s.name}-${sizeName}-${theme}.png`), ref);
        const got = await shoot('site');
        fs.writeFileSync(path.join(OUT, `${s.name}-${sizeName}-${theme}.site.png`), got);
        const a = PNG.sync.read(ref), b = PNG.sync.read(got);
        expect(`${b.width}x${b.height}`, 'page dimensions').toBe(`${a.width}x${a.height}`);
        const diff = new PNG({ width: a.width, height: a.height });
        const n = pixelmatch(a.data, b.data, diff.data, a.width, a.height, { threshold: 0.1 });
        const ratio = n / (a.width * a.height);
        if (ratio > TOLERANCE) { fs.writeFileSync(path.join(OUT, `${s.name}-${sizeName}-${theme}.diff.png`), PNG.sync.write(diff)); fs.writeFileSync(path.join(OUT, `${s.name}-${sizeName}-${theme}.site.png`), got); }
        expect(ratio, `pixel difference ${(ratio * 100).toFixed(2)}%`).toBeLessThanOrEqual(TOLERANCE);
      });
    }
  }
}
