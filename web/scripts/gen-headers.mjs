/* Post-build: writes web/vercel.json with a strict CSP for every route.
   Next's static export emits small inline <script>s (and React writes style="" attributes) whose content differs per page,
   so each route's CSP allows exactly those by sha256 hash, never 'unsafe-inline'.
   Locally this rewrites vercel.json (commit the result). On Vercel (VERCEL=1) it only VERIFIES the committed file and fails
   the deploy if it is stale, so a site that its own CSP would break is never published. */
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

const OUT = fileURLToPath(new URL('../out/', import.meta.url));
const TARGET = fileURLToPath(new URL('../vercel.json', import.meta.url));
const ROUTES = ['overview', 'kpis', 'insights', 'risk', 'activation', 'share'];
const sha = (s) => `'sha256-${createHash('sha256').update(s).digest('base64')}'`;
const unesc = (s) => s.replace(/&quot;/g, '"').replace(/&amp;/g, '&').replace(/&#x27;/g, "'").replace(/&lt;/g, '<').replace(/&gt;/g, '>');

function headersFor(file) {
  const html = readFileSync(OUT + file, 'utf8');
  const scripts = [...html.matchAll(/<script(?![^>]*\ssrc=)[^>]*>([\s\S]*?)<\/script>/g)].map((m) => sha(m[1]));
  const styles = [...new Set([...html.matchAll(/\sstyle="([^"]*)"/g)].map((m) => unesc(m[1])))].map(sha);
  const csp = [
    "default-src 'self'", "img-src 'self' data:", "style-src 'self'",
    `style-src-attr 'unsafe-hashes' ${styles.join(' ')}`.trim(),
    `script-src 'self' ${scripts.join(' ')}`.trim(),
    "base-uri 'none'", "form-action 'self'", "frame-ancestors 'none'",
  ].join('; ');
  return [
    { key: 'Content-Security-Policy', value: csp },
    { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
    { key: 'X-Content-Type-Options', value: 'nosniff' },
    { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
    { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
  ];
}

const config = {
  $schema: 'https://openapi.vercel.sh/vercel.json',
  cleanUrls: false,
  trailingSlash: true,
  redirects: [{ source: '/', destination: '/overview/', permanent: false }],
  headers: [
    ...ROUTES.map((r) => ({ source: `/${r}(/)?`, headers: headersFor(`${r}/index.html`) })),
    // everything else is served the 404 page
    { source: `/((?!${ROUTES.join('|')}|_next|fonts|data|favicon.svg|theme-init.js).*)`, headers: headersFor('404.html') },
  ],
};
const next = JSON.stringify(config, null, 2) + '\n';

if (process.env.VERCEL) {
  const cur = existsSync(TARGET) ? readFileSync(TARGET, 'utf8') : '';
  if (cur !== next) {
    console.error('vercel.json is out of date with this build (CSP hashes changed). Run `npm run build` locally and commit web/vercel.json.');
    process.exit(1);
  }
  console.log('vercel.json CSP hashes verified');
} else {
  writeFileSync(TARGET, next);
  console.log('wrote web/vercel.json');
}
