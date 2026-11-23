import path from 'node:path';
import { fileURLToPath } from 'node:url';
const root = path.dirname(fileURLToPath(import.meta.url));

/** Static export only: no server code, no API routes, no runtime secrets. */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
  trailingSlash: true,
  reactStrictMode: true,
  poweredByHeader: false,
  generateBuildId: async () => 'streakforge', // deterministic, so CSP hashes in vercel.json stay valid
  // '@/x' -> src/x (matches only the '@/' prefix, so '@fontsource/...' is untouched)
  webpack(config, { webpack }) {
    config.plugins.push(new webpack.NormalModuleReplacementPlugin(/^@\//, (r) => { r.request = path.join(root, 'src', r.request.slice(2)); }));
    return config;
  },
};
export default nextConfig;
