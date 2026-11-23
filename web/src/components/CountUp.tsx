'use client';
import { useEffect, useRef } from 'react';
import { useApp } from '@/lib/app';

/** Counts up the first time it scrolls into view; re-counts from the shown value when `to` changes. */
export function CountUp({ to, fmt }: { to: number; fmt: (v: number) => string }) {
  const ref = useRef<HTMLDivElement>(null);
  const cur = useRef(0);
  const { rm } = useApp();
  useEffect(() => {
    const el = ref.current!; let id = 0;
    const run = () => {
      if (rm) { cur.current = to; el.textContent = fmt(to); return; }
      const from = cur.current, t0 = performance.now();
      const f = (t: number) => { const p = Math.min(1, (t - t0) / 1100), e = 1 - Math.pow(1 - p, 3); cur.current = from + (to - from) * e; el.textContent = fmt(cur.current); if (p < 1) id = requestAnimationFrame(f); };
      id = requestAnimationFrame(f);
    };
    const io = new IntersectionObserver((es) => { if (es[0].isIntersecting) { run(); io.disconnect(); } });
    io.observe(el);
    return () => { io.disconnect(); cancelAnimationFrame(id); };
  }, [to, rm]); // eslint-disable-line react-hooks/exhaustive-deps
  return <div className="num" ref={ref}>0</div>;
}
