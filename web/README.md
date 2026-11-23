# StreakForge web

Static Next.js (App Router, `output: 'export'`) site that reproduces `docs/prototype/streakforge_prototype.html`.
No server code, database, API routes, analytics, third-party scripts or CDN. The Streamlit app in `streamlit_app/` is untouched.

## Run

```bash
# 1. export the data the site reads (repo root; needs pandas, see requirements.txt)
python src/export_web_data.py        # writes web/public/data/*.json from data/processed/*.csv

# 2. build and serve
cd web && npm install
npm run build                        # next build + scripts/gen-headers.mjs -> out/ and web/vercel.json
npm start                            # serves out/ on http://localhost:3100

# 3. tests (build first)
npx playwright install chromium
npm test                             # screenshots (vs the prototype), behaviour, axe
```

## Deploy (Vercel)

1. Import the GitHub repo in Vercel. Framework preset: **Next.js** (auto-detected).
2. Set **Root Directory** to `web`. Leave build, install and output settings at their defaults (`npm run build`; Next.js serves the static export).
3. Node 20 or newer.

Security headers live in `web/vercel.json`: a strict CSP per route plus HSTS, nosniff, Referrer-Policy and Permissions-Policy. The CSP allows Next's small inline scripts and React's inline `style=""` attributes by sha256 hash, never `'unsafe-inline'`.

**Whenever code or data changes, run `npm run build` locally and commit the updated `web/vercel.json`.** Builds are deterministic (fixed build id). On Vercel the build only *verifies* the committed file and fails the deploy if the hashes are stale, so a site its own CSP would break is never published.

## Security headers (as set in vercel.json)

```
Content-Security-Policy: default-src 'self'; img-src 'self' data:; style-src 'self'; style-src-attr 'unsafe-hashes' <hashes>; script-src 'self' <hashes>; base-uri 'none'; form-action 'self'; frame-ancestors 'none'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

## Notes

- Fonts are the exact woff2 files embedded in the prototype (Big Shoulders Display 800, Hanken Grotesk 400-700, IBM Plex Mono 400/500; latin + latin-ext), self-hosted from `public/fonts`.
- Display copy that the notebooks do not produce (KPI definitions, reading notes, insight wording) lives in `src/web_copy.json`; every number comes from the exported JSON.
- The day-by-day split of week one in the Field is illustrative and labelled so.
- Email export is not built: the card shows "Under development" with a disabled button.
