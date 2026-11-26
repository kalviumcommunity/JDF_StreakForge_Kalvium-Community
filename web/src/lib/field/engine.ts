/* The Field: one canvas, N dots, written pixel-by-pixel into a Uint32Array frame buffer.
   Ported literally from the prototype's Field module (timings, easing, layout maths). */
import type { AsOf, Risk } from '../types';

export interface FieldConfig { N: number; nAct: number; nAP: number; nAD: number; segCounts: number[]; risk: Risk[] }
export interface FieldLive { day: number; asof: AsOf }

type RGB = [number, number, number];
const P = [0.38, 0.17, 0.12, 0.1, 0.08, 0.06, 0.05, 0.04];

export function rng(a: number) {
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function shuffled(seed: number, N: number) {
  const r = rng(seed), a = Array.from({ length: N }, (_, i) => i);
  for (let i = N - 1; i > 0; i--) { const j = (r() * (i + 1)) | 0; [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
const ease = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const hex = (h: string): RGB => { h = h.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; };
const css = (v: string) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();

export class FieldEngine {
  scene = 4;
  private cv!: HTMLCanvasElement; private ctx!: CanvasRenderingContext2D; private tipEl!: HTMLElement;
  private W = 0; private H = 0; private dpr = 1; private img!: ImageData; private buf!: Uint32Array;
  private rows = 1; private cols = 1; private s = 8; private vis = true; private running = false; private hover = -1;
  private readonly N: number;
  private px: Float32Array; private py: Float32Array; private sx: Float32Array; private sy: Float32Array;
  private tx: Float32Array; private ty: Float32Array; private dl: Float32Array; private sz: Float32Array; private tsz: Float32Array;
  private c: Float32Array; private tc: Float32Array;
  private act: Uint8Array; private aday: Uint8Array; private seg: Uint8Array; private aP: Uint8Array; private aD: Uint8Array;
  private risk12: number[] = []; private order: number[][] = [[], [], [], [], []];
  private t0 = 0; private dur = 1100; private bgc: RGB = [244, 241, 234];
  private cols_t!: Record<string, RGB>; private emberCss = ''; private inkCss = ''; private monoCss = '';
  private cleanup: Array<() => void> = [];
  private raf = 0;

  constructor(private cfg: FieldConfig, private live: () => FieldLive, private rm: boolean) {
    const N = (this.N = cfg.N);
    this.px = new Float32Array(N); this.py = new Float32Array(N); this.sx = new Float32Array(N); this.sy = new Float32Array(N);
    this.tx = new Float32Array(N); this.ty = new Float32Array(N); this.dl = new Float32Array(N); this.sz = new Float32Array(N); this.tsz = new Float32Array(N);
    this.c = new Float32Array(N * 4); this.tc = new Float32Array(N * 4);
    this.act = new Uint8Array(N); this.aday = new Uint8Array(N); this.seg = new Uint8Array(N); this.aP = new Uint8Array(N); this.aD = new Uint8Array(N);
    this.assign();
  }

  private assign() {
    const { N, nAct, nAP, nAD, segCounts } = this.cfg;
    const p1 = shuffled(11, N), p2 = shuffled(22, N), p3 = shuffled(33, N);
    let k = 0;
    P.forEach((p, d) => { const n = d === 7 ? nAct - k : Math.round(nAct * p); for (let i = 0; i < n; i++) { this.act[p1[k]] = 1; this.aday[p1[k]] = d; k++; } });
    p2.slice(0, nAP).forEach((i) => (this.aP[i] = 1));
    p2.slice(0, nAD).forEach((i) => (this.aD[i] = 1));
    let q = 0;
    segCounts.forEach((n, si) => { for (let i = 0; i < n && q < N; i++) this.seg[p3[q++]] = si; });
    const al = p2.slice(0, nAP), step = nAP / 12;
    this.risk12 = Array.from({ length: 12 }, (_, j) => al[Math.round(j * step + step / 3)]);
    const { act, aday, aP, aD, seg } = this;
    const key = [() => 0, (i: number) => (act[i] ? aday[i] : 9), (i: number) => (aP[i] ? 0 : aD[i] ? 1 : 2), (i: number) => seg[i], (i: number) => (aP[i] ? 0 : aD[i] ? 1 : 2)];
    key.forEach((kf, si) => {
      this.order[si] = si === 0 ? Array.from({ length: N }, (_, i) => i) : Array.from({ length: N }, (_, i) => i).sort((a, b) => kf(a) - kf(b) || a - b);
    });
  }

  palette() {
    this.bgc = hex(css('--card'));
    this.cols_t = { dot: hex(css('--dot')), ember: hex(css('--ember')), champ: hex(css('--champ')), loyal: hex(css('--loyal')), dorm: hex(css('--dorm')), risk: hex(css('--ember')), amber: hex(css('--amber')) };
    this.emberCss = css('--ember'); this.inkCss = css('--ink'); this.monoCss = css('--mono');
  }
  private layout() {
    const { N } = this, { W, H } = this;
    let s = Math.sqrt((W * H * 0.96) / N);
    let rows = Math.max(1, Math.floor(H / s)), cols = Math.ceil(N / rows);
    while (cols * s > W - 8) { s *= 0.985; rows = Math.max(1, Math.floor(H / s)); cols = Math.ceil(N / rows); }
    this.s = s; this.rows = rows; this.cols = cols;
  }
  private slot(si: number, k: number): [number, number] {
    const { s, rows, cols, W, H, N } = this;
    const ox = (W - cols * s) / 2, oy = (H - rows * s) / 2;
    if (si === 0) {
      const cc = k % cols, rr = (k / cols) | 0;
      return [ox + cc * s + s / 2, oy + rr * s * (rows * cols > 0 ? (rows * s) / (Math.ceil(N / cols) * s) : 1) + s / 2];
    }
    return [ox + ((k / rows) | 0) * s + s / 2, oy + (k % rows) * s + s / 2];
  }
  private targets(si: number) {
    const { N, W, H, s, aP, tx, ty, tsz } = this;
    if (si === 4) {
      const nAP = this.cfg.nAP, alive: number[] = [];
      this.order[2].forEach((i) => { if (aP[i]) alive.push(i); });
      const s4 = Math.sqrt((W * H * 0.62) / nAP), r4 = Math.max(1, Math.floor((H * 0.88) / s4)), c4 = Math.ceil(nAP / r4);
      const ox = (W - c4 * s4) / 2, oy = (H - r4 * s4) / 2;
      alive.forEach((i, k) => { tx[i] = ox + ((k / r4) | 0) * s4 + s4 / 2; ty[i] = oy + (k % r4) * s4 + s4 / 2; tsz[i] = s4 * 0.58; });
      for (let i = 0; i < N; i++) if (!aP[i]) { const p = this.slot(0, i); tx[i] = p[0]; ty[i] = p[1]; tsz[i] = s * 0.5; }
      this.risk12.forEach((i) => { tsz[i] = tsz[i] * 1.35; });
      return;
    }
    this.order[si].forEach((i, k) => { const p = this.slot(si, k); tx[i] = p[0]; ty[i] = p[1]; tsz[i] = s * 0.62; });
  }
  private colors() {
    const { N, act, aday, aP, aD, seg, tc } = this, sc = this.scene, C = this.cols_t, { day, asof } = this.live();
    for (let i = 0; i < N; i++) {
      let col = C.dot, a = 0.5;
      if (sc === 0) a = 0.5;
      else if (sc === 1) { if (act[i]) { col = C.ember; a = aday[i] <= day ? 1 : 0.28; } else { col = C.dot; a = 0.22; } }
      else if (sc === 2) { if (aP[i]) { col = C.champ; a = 1; } else if (aD[i] && asof === 'data') { col = C.amber; a = 0.95; } else { col = C.dorm; a = 0.28; } }
      else if (sc === 3) { col = [C.champ, C.loyal, C.risk, C.dorm][seg[i]]; a = 0.92; }
      else { if (aP[i]) { col = C.champ; a = 0.9; } else { col = C.dorm; a = 0.06; } }
      const o = i * 4; tc[o] = col[0]; tc[o + 1] = col[1]; tc[o + 2] = col[2]; tc[o + 3] = a;
    }
    if (sc === 4) this.risk12.forEach((i) => { const o = i * 4; tc[o] = C.ember[0]; tc[o + 1] = C.ember[1]; tc[o + 2] = C.ember[2]; tc[o + 3] = 1; });
  }
  go(si: number, instant = false) {
    this.scene = si; this.palette();
    const { N, px, py, sx, sy, tx, ty, dl, sz, tsz, W } = this;
    for (let i = 0; i < N; i++) { sx[i] = px[i]; sy[i] = py[i]; }
    this.targets(si); this.colors();
    const r = rng(7);
    for (let i = 0; i < N; i++) dl[i] = (tx[i] / W) * 380 + r() * 120;
    this.t0 = performance.now(); this.dur = this.rm || instant ? 0 : 1100;
    if (this.dur === 0) { for (let i = 0; i < N; i++) { px[i] = tx[i]; py[i] = ty[i]; sz[i] = tsz[i]; } this.c.set(this.tc); }
    this.kick();
  }
  recolor() { this.colors(); this.kick(); }
  private kick() { if (!this.running && this.vis) { this.running = true; this.raf = requestAnimationFrame(this.frame); } }
  private frame = (now: number) => {
    this.running = false; if (!this.vis) return;
    const { N, px, py, sx, sy, tx, ty, dl, sz, tsz, c, tc } = this;
    let moving = false;
    if (this.dur > 0) {
      for (let i = 0; i < N; i++) {
        const p = Math.min(1, Math.max(0, (now - this.t0 - dl[i]) / this.dur)), e = ease(p);
        px[i] = sx[i] + (tx[i] - sx[i]) * e; py[i] = sy[i] + (ty[i] - sy[i]) * e; if (p < 1) moving = true;
      }
      for (let i = 0; i < N; i++) sz[i] += (tsz[i] - sz[i]) * 0.12;
    }
    let cm = false;
    for (let k = 0; k < N * 4; k++) { const d = tc[k] - c[k]; if (d > 0.4 || d < -0.4) { c[k] += d * (this.rm ? 1 : 0.14); cm = true; } else c[k] = tc[k]; }
    this.draw(now);
    if (moving || cm || (this.scene === 4 && !this.rm)) { this.running = true; this.raf = requestAnimationFrame(this.frame); }
  };
  private draw(now: number) {
    const { img, ctx, buf: b, c, sz, px, py, N, bgc, dpr } = this;
    const w = img.width, h = img.height;
    const bg = (255 << 24) | (bgc[2] << 16) | (bgc[1] << 8) | bgc[0]; b.fill(bg);
    for (let pass = 0; pass < 2; pass++) for (let i = 0; i < N; i++) {
      const o = i * 4, a = c[o + 3]; if (a < 0.02 || (a >= 0.5) !== (pass === 1)) continue;
      const r = (bgc[0] + (c[o] - bgc[0]) * a) | 0, g = (bgc[1] + (c[o + 1] - bgc[1]) * a) | 0, bl = (bgc[2] + (c[o + 2] - bgc[2]) * a) | 0, v = (255 << 24) | (bl << 16) | (g << 8) | r;
      const d = Math.max(2, Math.round(sz[i] * dpr)), x0 = Math.round(px[i] * dpr - d / 2), y0 = Math.round(py[i] * dpr - d / 2);
      for (let yy = 0; yy < d; yy++) { const y = y0 + yy; if (y < 0 || y >= h) continue; const row = y * w; for (let xx = 0; xx < d; xx++) { const x = x0 + xx; if (x >= 0 && x < w) b[row + x] = v; } }
    }
    ctx.putImageData(img, 0, 0);
    if (this.scene === 4) {
      const pulse = this.rm ? 0 : (Math.sin(now / 380) + 1) / 2;
      ctx.lineWidth = 1.5 * dpr; ctx.strokeStyle = this.emberCss; ctx.fillStyle = this.inkCss; ctx.font = `500 ${11 * dpr}px ${this.monoCss}`;
      this.risk12.forEach((i, j) => {
        const x = px[i] * dpr, y = py[i] * dpr, r = (9 + pulse * 6) * dpr;
        ctx.globalAlpha = 1 - pulse * 0.5; ctx.beginPath(); ctx.arc(x, y, r, 0, 7); ctx.stroke(); ctx.globalAlpha = 1;
        ctx.fillText(String(j + 1).padStart(2, '0'), x + 13 * dpr, y - 10 * dpr);
      });
    }
    if (this.hover >= 0) { ctx.globalAlpha = 1; ctx.lineWidth = 1.5 * dpr; ctx.strokeStyle = this.inkCss; ctx.beginPath(); ctx.arc(px[this.hover] * dpr, py[this.hover] * dpr, 7 * dpr, 0, 7); ctx.stroke(); }
  }
  private status(i: number) {
    const sc = this.scene, { act, aday, aP, aD, seg } = this, { asof } = this.live();
    if (sc === 1) return act[i] ? `Lit up on day ${aday[i]} (illustrative day)` : 'No event in first 7 days';
    if (sc === 2) return aP[i] ? 'Active at pipeline date' : aD[i] ? (asof === 'data' ? 'Active at data-realistic date only' : 'Churned at pipeline date') : 'Churned either way';
    if (sc === 3) return ['Champion', 'Loyal / Engaged', 'At Risk', 'Dormant / Lapsed'][seg[i]];
    if (sc === 4) { const j = this.risk12.indexOf(i); return j >= 0 ? `Flagged high-risk #${j + 1}` : aP[i] ? 'Active member' : 'Churned'; }
    return act[i] ? 'Activated in week one' : 'Did not activate in week one';
  }
  private onMove = (e: MouseEvent) => {
    const r = this.cv.getBoundingClientRect(), mx = e.clientX - r.left, my = e.clientY - r.top;
    let best = -1, bd = 100;
    for (let i = 0; i < this.N; i++) { const dx = this.px[i] - mx, dy = this.py[i] - my, d = dx * dx + dy * dy; if (d < bd) { bd = d; best = i; } }
    this.hover = best;
    if (best >= 0) { this.tipEl.textContent = `Synthetic member #${best + 1} · ${this.status(best)}`; this.tipEl.style.left = this.px[best] + 'px'; this.tipEl.style.top = this.py[best] + 'px'; this.tipEl.classList.add('on');
      const tw = this.tipEl.offsetWidth, th = this.tipEl.offsetHeight;
      const x = this.px[best] + 12 + tw > this.W ? `calc(-100% - 12px)` : '12px'; // flip left near the right edge
      const y = this.py[best] - th - 6 < 0 ? '12px' : '-120%'; // drop below near the top edge
      this.tipEl.style.transform = `translate(${x},${y})`; }
    else this.tipEl.classList.remove('on');
    this.kick();
  };
  private resize() {
    const r = this.cv.getBoundingClientRect(); this.W = r.width; this.H = r.height; this.dpr = Math.min(2, window.devicePixelRatio || 1);
    this.cv.width = Math.round(this.W * this.dpr); this.cv.height = Math.round(this.H * this.dpr);
    this.img = this.ctx.createImageData(this.cv.width, this.cv.height); this.buf = new Uint32Array(this.img.data.buffer);
    this.layout(); this.go(this.scene, true);
  }
  init(cv: HTMLCanvasElement, tip: HTMLElement, scene: number) {
    this.cv = cv; this.ctx = cv.getContext('2d')!; this.tipEl = tip; this.scene = scene;
    this.palette(); this.resize();
    const leave = () => { this.hover = -1; this.tipEl.classList.remove('on'); this.kick(); };
    cv.addEventListener('mousemove', this.onMove); cv.addEventListener('mouseleave', leave);
    const ro = new ResizeObserver(() => { if (cv.isConnected) { const r = cv.getBoundingClientRect(); if (Math.abs(r.width - this.W) > 1) this.resize(); } }); ro.observe(cv);
    const io = new IntersectionObserver((es) => { this.vis = es[0].isIntersecting; if (this.vis) this.kick(); }); io.observe(cv);
    this.cleanup.push(() => { cv.removeEventListener('mousemove', this.onMove); cv.removeEventListener('mouseleave', leave); ro.disconnect(); io.disconnect(); cancelAnimationFrame(this.raf); });
  }
  destroy() { this.cleanup.forEach((f) => f()); this.cleanup = []; this.vis = false; }
  counts(d: number) { let n = 0; for (let i = 0; i < this.N; i++) if (this.act[i] && this.aday[i] <= d) n++; return n; }
}
