# StreakForge web

Live: https://jdf-streakforge-kalvium-community.netlify.app/overview/

Static Next.js (App Router, `output: 'export'`) site that reproduces `docs/prototype/streakforge_prototype.html`.
No server code, database, API routes, analytics, third-party scripts or CDN. The Streamlit app in `streamlit_app/` is untouched.

## Run

```bash
# 1. export the data the site reads (repo root; needs pandas, see requirements.txt)
python src/export_web_data.py        # writes web/public/data/*.json from data/processed/*.csv

# 2. build and serve
cd web && npm install
npm run build                        # next build + scripts/gen-headers.mjs -> out/ (with out/_headers)
npm start                            # serves out/ on http://localhost:3100

# 3. tests (build first)
npx playwright install chromium
npm test                             # screenshots (vs the prototype), behaviour, axe
```

## Deploy (Netlify)

`netlify.toml` at the repo root holds the settings: base `web`, build `npm ci && npm run build`, publish `out`, Node 22, and a redirect from `/` to `/overview/`.
In Netlify choose "Import from Git", pick the repo and branch, and accept the detected settings.

Security headers are written to `out/_headers` on every build by `scripts/gen-headers.mjs`. The CSP allows Next's small inline scripts and React's inline `style=""` attributes by sha256 hash (never `'unsafe-inline'`), so the hashes always match the files being published. The CSP is set on the six pages and the 404 page; unknown URLs served the 404 page get the other headers but no CSP.

## Security headers

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
