export type Theme = 'light' | 'dark';
export const getTheme = (): Theme => (document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light');
/** Applies and saves the theme (localStorage guarded: it can throw in private windows). */
export function applyTheme(t: Theme) {
  document.documentElement.dataset.theme = t;
  try { localStorage.setItem('sf-theme', t); } catch { /* ignore */ }
  const meta = document.querySelector('meta[name=theme-color]') as HTMLMetaElement | null;
  if (meta) meta.content = t === 'dark' ? '#151413' : '#F4F1EA';
  window.dispatchEvent(new Event('sf-theme'));
}
