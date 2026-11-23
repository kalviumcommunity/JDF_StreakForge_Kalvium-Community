export const nf = (n: number) => Math.round(n).toLocaleString('en-IN');
export const pc = (x: number, d = 1) => (x * 100).toFixed(d) + '%';
export const inr = (n: number) => '₹' + nf(n);
export const esc = (s: unknown) =>
  String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c] as string));
export const slug = () => new Date().toISOString().slice(0, 10);
