'use client';
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import type { AsOf, SiteData, Sim } from './types';
import { metrics, type Metrics } from './metrics';

interface Ctx {
  data: SiteData; m: Metrics;
  asof: AsOf; setAsof: (a: AsOf) => void;
  sim: Sim; setSim: (s: Sim) => void;
  toast: (msg: string) => void; toastMsg: { text: string; on: boolean };
  pending: React.MutableRefObject<string | null>;
  rm: boolean;
}
const AppCtx = createContext<Ctx>(null as unknown as Ctx);
export const useApp = () => useContext(AppCtx);

export function AppProvider({ data, children }: { data: SiteData; children: ReactNode }) {
  const [asof, setAsof] = useState<AsOf>('pipeline');
  const [sim, setSim] = useState<Sim>('');
  const [toastMsg, setToastMsg] = useState({ text: '', on: false });
  const [rm, setRm] = useState(false);
  const pending = useRef<string | null>(null);
  const tt = useRef<ReturnType<typeof setTimeout>>(undefined);
  const m = useMemo(() => metrics(data), [data]);
  useEffect(() => {
    const q = matchMedia('(prefers-reduced-motion: reduce)');
    setRm(q.matches);
    const f = () => setRm(q.matches);
    q.addEventListener('change', f);
    return () => q.removeEventListener('change', f);
  }, []);
  const toast = useCallback((text: string) => {
    setToastMsg({ text, on: true });
    clearTimeout(tt.current);
    tt.current = setTimeout(() => setToastMsg((t) => ({ ...t, on: false })), 2600);
  }, []);
  const value = useMemo(() => ({ data, m, asof, setAsof, sim, setSim, toast, toastMsg, pending, rm }), [data, m, asof, sim, toast, toastMsg, rm]);
  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}
