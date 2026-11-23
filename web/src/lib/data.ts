import 'server-only';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import type { SiteData } from './types';

/** Build-time loader: reads the exported JSON in public/data (written by src/export_web_data.py). */
function read<T>(name: string): T {
  return JSON.parse(readFileSync(join(process.cwd(), 'public', 'data', `${name}.json`), 'utf8')) as T;
}

export function loadData(): SiteData {
  return {
    kpis: read('kpis'), insights: read('insights'), branches: read('branches'), cohorts: read('cohorts'),
    segments: read('segments'), risk: read('at_risk'), funnel: read('funnel'), rfm: read('rfm'),
  };
}
