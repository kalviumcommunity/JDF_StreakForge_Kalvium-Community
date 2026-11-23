/* Post-build: writes out/_headers (Netlify / Cloudflare Pages format) with a strict CSP.
   Next's static export emits small inline bootstrap <script>s whose content differs per page,
   so each route gets a CSP that allows exactly those scripts by sha256 hash (never 'unsafe-inline'). */
import { createHash } from 'node:crypto';
import { readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs';
import { join, relative } from 'node:path';

const OUT = new URL('../out', import.meta.url).pathname;
const walk = (d) => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? walk(join(d, f)) : [join(d, f)]));
const common = [
  'Strict-Transport-Security: max-age=31536000; includeSubDomains',
  'X-Content-Type-Options: nosniff',
  'Referrer-Policy: strict-origin-when-cross-origin',
  'Permissions-Policy: camera=(), microphone=(), geolocation=()',
];
const hashes = (html, re) => [...html.matchAll(re)].map((m) => `'sha256-${createHash('sha256').update(m[1]).digest('base64')}'`);
let out = '';
for (const f of walk(OUT).filter((p) => p.endsWith('.html'))) {
  const html = readFileSync(f, 'utf8');
  const scripts = hashes(html, /<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g);
  // Inline style="" attributes are written by React; allow them by hash (style-src-attr) instead of 'unsafe-inline'.
  const styleAttrs = [...new Set([...html.matchAll(/\sstyle="([^"]*)"/g)].map((m) => m[1].replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&#x27;/g, "'")))]
    .map((s) => `'sha256-${createHash('sha256').update(s).digest('base64')}'`);
  const csp = [
    "default-src 'self'",
    "img-src 'self' data:",
    "style-src 'self'",
    `style-src-attr 'unsafe-hashes' ${styleAttrs.join(' ')}`.trim(),
    `script-src 'self' ${scripts.join(' ')}`.trim(),
    "base-uri 'none'", "form-action 'self'", "frame-ancestors 'none'",
  ].join('; ');
  const route = '/' + relative(OUT, f).replace(/index\.html$/, '').replace(/\.html$/, '');
  out += `${route}\n  Content-Security-Policy: ${csp}\n${common.map((h) => `  ${h}`).join('\n')}\n\n`;
}
writeFileSync(join(OUT, '_headers'), out);
console.log(`wrote out/_headers for ${out.split('\n\n').length - 1} pages`);
