'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useRef } from 'react';
import type { ReactNode, MouseEvent } from 'react';
import { useApp } from '@/lib/app';
import { applyTheme, getTheme } from '@/lib/theme';
import { useState } from 'react';
import { SimView } from './States';

export const NAV = [
  ['overview', 'Overview'], ['kpis', 'KPI ledger'], ['insights', 'Insights'],
  ['risk', 'Risk & branches'], ['activation', 'Activation'], ['share', 'Share & export'],
] as const;

export function SkipLink() { return <a className="skip" href="#main">Skip to content</a>; }

export function TopBar() {
  const path = usePathname() || '';
  const [dark, setDark] = useState(false);
  useEffect(() => {
    setDark(getTheme() === 'dark');
    const f = () => setDark(getTheme() === 'dark');
    window.addEventListener('sf-theme', f);
    return () => window.removeEventListener('sf-theme', f);
  }, []);
  return (
    <header className="top">
      <div className="wrap">
        <Link className="brand" href="/overview/" aria-label="StreakForge home" scroll={false}>
          <svg viewBox="0 0 32 32" aria-hidden="true"><g fill="currentColor"><rect x="3" y="3" width="8" height="8" /><rect x="12" y="3" width="8" height="8" /><rect x="3" y="12" width="8" height="8" /><rect x="3" y="21" width="8" height="8" /></g><rect x="21" y="3" width="8" height="8" fill="var(--ember)" /></svg>
          <span>StreakForge</span>
        </Link>
        <nav className="nav" aria-label="Primary" id="nav">
          {NAV.map(([r, label]) => (
            <Link key={r} href={`/${r}/`} scroll={false} aria-current={path.replace(/\/$/, '') === `/${r}` ? 'page' : 'false'}>{label}</Link>
          ))}
        </nav>
        <div className="tools">
          <button className="icon-btn" id="themeBtn" aria-pressed={dark} aria-label="Dark theme" onClick={() => applyTheme(getTheme() === 'dark' ? 'light' : 'dark')}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z" /></svg>
          </button>
        </div>
      </div>
    </header>
  );
}

export function ProvenanceStrip() {
  const { asof, setAsof, m } = useApp();
  return (
    <div className="prov" role="note" aria-label="Data provenance">
      <div className="wrap">
        <span className="mono">Synthetic dataset <b>{m.N.toLocaleString('en-IN')} members</b></span>
        <span className="mono"><b>40</b> branches</span>
        <span className="mono">Events <b>2021-01 to 2025-10-05</b></span>
        <span className="mono" id="provAsof">{asof === 'pipeline' ? 'Pipeline' : 'Realistic'} as-of <b>{asof === 'pipeline' ? '2026-08-14' : '2025-10-05'}</b></span>
        <div className="seg" role="group" aria-label="As-of date">
          <button data-asof="pipeline" aria-pressed={asof === 'pipeline'} onClick={() => setAsof('pipeline')}>Pipeline date</button>
          <button data-asof="data" aria-pressed={asof === 'data'} onClick={() => setAsof('data')}>Data-realistic date</button>
        </div>
      </div>
    </div>
  );
}

export function Toast() {
  const { toastMsg } = useApp();
  return <div className={'toast' + (toastMsg.on ? ' on' : '')} id="toast" role="status" aria-live="polite">{toastMsg.text}</div>;
}

/** Link that remembers an in-page anchor to scroll to after navigation (the prototype's data-scroll). */
export function AnchorLink({ href, anchor, className, children, id, style }: { href: string; anchor?: string; className?: string; children: ReactNode; id?: string; style?: React.CSSProperties }) {
  const { pending, rm } = useApp();
  const path = usePathname() || '';
  const onClick = (e: MouseEvent) => {
    if (!anchor) return;
    if (path.replace(/\/$/, '') === href.replace(/\/$/, '')) {
      e.preventDefault();
      document.getElementById(anchor)?.scrollIntoView({ behavior: rm ? 'auto' : 'smooth', block: 'start' });
      return;
    }
    pending.current = anchor;
  };
  return <Link id={id} style={style} className={className} href={href} scroll={false} onClick={onClick}>{children}</Link>;
}

/** <main>: resets preview states on navigation, scrolls (to top or a pending anchor) and runs scroll reveals. */
export function Main({ children }: { children: ReactNode }) {
  const { sim, setSim, pending, rm } = useApp();
  const path = usePathname();
  const ref = useRef<HTMLElement>(null);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) first.current = false; else setSim('');
    const id = pending.current; pending.current = null;
    if (id) { const t = setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: rm ? 'auto' : 'smooth', block: 'start' }), 120); return () => clearTimeout(t); }
    window.scrollTo(0, 0);
  }, [path]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => {
    const nodes = Array.from(ref.current?.querySelectorAll('.reveal,.fr') ?? []);
    if (rm) { nodes.forEach((n) => n.classList.add('in')); return; }
    const io = new IntersectionObserver((es) => es.forEach((e) => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { threshold: 0.12 });
    nodes.forEach((n) => io.observe(n));
    return () => io.disconnect();
  }, [path, sim, rm]);
  return <main id="main" tabIndex={-1} ref={ref}>{sim ? <SimView sim={sim} onReset={() => setSim('')} /> : children}</main>;
}
