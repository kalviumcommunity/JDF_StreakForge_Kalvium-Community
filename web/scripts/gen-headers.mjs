/* Post-build: writes out/_headers (Netlify format) with a strict CSP for every page.
   Next's static export emits small inline <script>s (and React writes style="" attributes) whose content differs per page,
   so each page's CSP allows exactly those by sha256 hash, never 'unsafe-inline'.
   Generated at build time on every deploy, so the hashes always match the files being published. */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const OUT = fileURLToPath(new URL('../out/', import.meta.url));
const ROUTES = ['overview', 'kpis', 'insights', 'risk', 'activation', 'share'];
const sha = (s) => `'sha256-${createHash('sha256').update(s).digest('base64')}'`;
const unesc = (s) => s.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');

function csp(file) {
  const html = readFileSync(OUT + file, 'utf8');
  const scripts = [...html.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => sha(m[1]));
  const styles = [...new Set([...html.matchAll(/\sstyle="([^"]*)"/g)].map((m) => unesc(m[1])))].map(sha);
  return [
    "default-src 'self'", "img-src 'self' data:", "style-src 'self'",
    `style-src-attr 'unsafe-hashes' ${styles.join(' ')}`.trim(),
    `script-src 'self' ${scripts.join(' ')}`.trim(),
    "base-uri 'none'", "form-action 'self'", "frame-ancestors 'none'",
  ].join('; ');
}

// Netlify merges every matching rule, so the CSP is set on exact page paths only and the rest goes on /*.
let out = `/*
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()

`;
for (const r of ROUTES) for (const path of [`/${r}/`, `/${r}/index.html`]) out += `${path}\n  Content-Security-Policy: ${csp(`${r}/index.html`)}\n\n`;
out += `/404.html\n  Content-Security-Policy: ${csp('404.html')}\n`;
writeFileSync(OUT + '_headers', out);
console.log('wrote out/_headers');
