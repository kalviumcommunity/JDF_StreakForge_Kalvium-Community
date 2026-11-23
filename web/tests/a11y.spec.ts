import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { PAGES } from './helpers';

for (const theme of ['light', 'dark']) for (const p of PAGES) {
  test(`axe · ${p} · ${theme}`, async ({ page }) => {
    await page.addInitScript((t) => localStorage.setItem('sf-theme', t), theme);
    await page.goto(`/${p}/`); await page.waitForLoadState('networkidle');
    const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa']).analyze();
    expect(r.violations.map((v) => `${v.id}: ${v.nodes.length} (${v.nodes[0].target})`)).toEqual([]);
  });
}
