'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { ReactNode } from 'react';
import { useApp } from '@/lib/app';
import { FieldEngine } from '@/lib/field/engine';
import { inr, nf, pc } from '@/lib/format';
import { AnchorLink } from './Shell';
import { TypeHeading } from './TypeHeading';

const LEG: Record<string, string> = { dot: 'var(--dot)', ember: 'var(--ember)', emberL: 'color-mix(in srgb,var(--ember) 30%,var(--card))', champ: 'var(--champ)', loyal: 'var(--loyal)', risk: 'var(--ember)', dorm: 'var(--dorm)', amber: 'var(--amber)' };
const TITLES = ['Everyone', 'The first seven days', 'Who is still here', 'Four kinds of member', 'Twelve to call'];
const LEGENDS: [string, string][][] = [
  [['dot', 'Member']],
  [['ember', 'Activated by this day'], ['emberL', 'Will activate later'], ['dot', 'Never activated']],
  [['champ', 'Active'], ['amber', 'Active at realistic date only'], ['dorm', 'Churned']],
  [['champ', 'Champions'], ['loyal', 'Loyal / Engaged'], ['risk', 'At Risk'], ['dorm', 'Dormant / Lapsed']],
  [['champ', 'Active'], ['ember', 'Flagged high-risk'], ['dorm', 'Churned']],
];

export function FieldStory() {
  const { data, m, asof, setAsof, toast, rm } = useApp();
  const [scene, setSceneState] = useState(4);
  const [day, setDay] = useState(7);
  const cv = useRef<HTMLCanvasElement>(null), tip = useRef<HTMLDivElement>(null);
  const eng = useRef<FieldEngine | null>(null);
  const live = useRef({ day, asof }); live.current = { day, asof };
  const playT = useRef<ReturnType<typeof setTimeout>>(undefined);
  const repT = useRef<ReturnType<typeof setTimeout>>(undefined);
  const stage = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const e = new FieldEngine({ N: m.N, nAct: m.nAct, nAP: m.nAP, nAD: m.nAD, segCounts: m.segCounts, risk: data.risk }, () => live.current, matchMedia('(prefers-reduced-motion: reduce)').matches);
    eng.current = e;
    e.init(cv.current!, tip.current!, 4);
    const th = () => { e.palette(); e.recolor(); };
    window.addEventListener('sf-theme', th);
    return () => { window.removeEventListener('sf-theme', th); e.destroy(); eng.current = null; clearTimeout(playT.current); clearTimeout(repT.current); };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { eng.current?.recolor(); }, [day, asof]);

  const setScene = useCallback((i: number) => { setSceneState(i); eng.current?.go(i); }, []);
  const play = () => {
    let i = 0;
    const next = () => { setScene(i); i++; if (i < 5) playT.current = setTimeout(next, 4200); };
    clearTimeout(playT.current); next();
    toast('Playing the five chapters. Click any chapter to take over.');
  };
  const replay = () => {
    clearTimeout(repT.current);
    let d = -1;
    const step = () => { d++; setDay(Math.min(7, d)); if (d < 7 && !rm) repT.current = setTimeout(step, 420); };
    step();
  };
  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
      const pos = (scene + (e.key === 'ArrowRight' ? 1 : 4)) % 5;
      setScene(pos);
      (stage.current?.querySelectorAll('button')[pos] as HTMLElement | undefined)?.focus();
    }
  };

  const hud: [number, string][] =
    scene === 0 ? [[m.N, 'members signed up']]
    : scene === 1 ? [[eng.current?.counts(day) ?? 0, 'activated by day ' + day], [m.N - m.nAct, 'never activated']]
    : scene === 2 ? (asof === 'pipeline' ? [[m.nAP, 'active members'], [m.N - m.nAP, 'churned']] : [[m.nAD, 'active members'], [m.N - m.nAD, 'churned']])
    : scene === 3 ? data.rfm.slice().sort((a, b) => b[1] - a[1]).slice(0, 2).map((r) => [r[1], r[0]] as [number, string])
    : [[12, 'flagged high-risk'], [m.nAP, 'active members']];

  const heading = [
    `${nf(m.N)} members. One dot each.`,
    `${nf(m.nAct)} lit up. ${nf(m.N - m.nAct)} stayed dark.`,
    asof === 'pipeline' ? `${nf(m.nAP)} active. The rest read as churned.` : `About ${nf(m.nAD)} active once the date is realistic.`,
    'Sorted by recency, frequency and spend.',
    `Of ${nf(m.nAP)} active members, twelve stand out.`,
  ][scene];

  const actPct = pc(m.nAct / m.N), dropPct = pc(1 - m.nAct / m.N);
  const body: ReactNode[] = [
    <><p>Each dot is a member who joined between <b>January 2021 and September 2025</b>, spread across <b>40 branches</b>. Hover over the field to meet one.</p><p>None of them is real. The data is synthetic, and every number in this page comes from the same generated set.</p></>,
    <><p><b>Only {actPct} of members log any activity within 7 days of joining.</b> That {dropPct} drop is the biggest step in the whole funnel, bigger than renewal or streak formation.</p><p>No channel, city tier or plan type explains it: every Cramér&apos;s V is below 0.1.</p></>,
    <><p>Churn means <b>the latest billing cycle ended more than 30 days before the as-of date</b>. The pipeline fixed that date at 2026-08-14, but the last real event is 2025-10-05.</p><p>Move the as-of date to the last real event and <b>churn falls from {pc(m.churnPipeline)} to {pc(m.churnData)}</b>. It is still high. It is no longer a crisis built on missing data.</p></>,
    <p>Quartile scoring on recency, frequency and money splits the base into four groups. <b>Even Champions show high churn</b>, which is another sign that the as-of date, not behaviour, is doing the damage.</p>,
    <><p>Scored on four signals (long silence, few events, falling trend, high spend per session) the active base splits into <b>487 low, 403 moderate, 109 elevated and 12 high</b>.</p><p>Most of the twelve joined, paid, logged one session and vanished, at <b>₹48,000 to ₹102,000 per session</b>. All twelve are real rows from the analysis.</p></>,
  ];
  const ctl: ReactNode[] = [
    <div className="callout"><b>Why a field of dots?</b> A table of {nf(m.N)} rows hides the shape. Here you can watch the shape change as each question is asked.</div>,
    <div className="ctl"><div className="ctl-row"><span className="lbl">Day since joining</span><span className="flag warn">Day split is illustrative</span></div>
      <input type="range" id="day" min={0} max={7} step={1} value={day} aria-label="Day since joining" aria-valuetext={`Day ${day}`} style={{ '--p': `${(day / 7) * 100}%` } as React.CSSProperties} onChange={(e) => setDay(+e.target.value)} />
      <div className="ticks"><span>Day 0</span><span>1</span><span>2</span><span>3</span><span>4</span><span>5</span><span>6</span><span>Day 7</span></div>
      <div className="ctl-row"><button className="btn sm" id="replay" onClick={replay}>Replay the week</button><span className="callout" style={{ border: 0, padding: 0 }}>The final <b>{nf(m.nAct)}</b> is measured. How those members spread across days 0 to 7 is modelled for the animation.</span></div></div>,
    <div className="ctl"><span className="lbl">As-of date</span>
      <div className="seg" style={{ margin: 0, width: 'max-content' }} role="group" aria-label="As-of date"><button data-asof="pipeline" aria-pressed={asof === 'pipeline'} onClick={() => setAsof('pipeline')}>Pipeline 2026-08-14</button><button data-asof="data" aria-pressed={asof === 'data'} onClick={() => setAsof('data')}>Last event 2025-10-05</button></div>
      <div className="callout"><b>{asof === 'pipeline' ? `${pc(m.churnPipeline)} churn` : `${pc(m.churnData)} churn`}.</b> {asof === 'pipeline' ? 'This is what the pipeline reports.' : 'The amber dots are members the pipeline wrote off only because 313 days of data were missing.'}</div></div>,
    <div className="ctl"><span className="lbl">Segment mix</span>
      {data.rfm.map((r) => <div className="ctl-row" style={{ justifyContent: 'space-between' }} key={r[0]}><span><i style={{ display: 'inline-block', width: 10, height: 10, background: `var(--${r[2]})`, marginRight: 8 }} />{r[0]}</span><span className="mono">{nf(r[1])} · {pc(r[1] / m.N)}</span></div>)}</div>,
    <div className="ctl"><span className="lbl">The shortlist · numbers match the rings</span>
      <div>{data.risk.map((r, i) => <div className="ctl-row" style={{ justifyContent: 'space-between', borderTop: '1px solid var(--line2)', padding: '6px 0' }} key={r.id}><span className="mono" style={{ color: 'var(--ink)' }}>{String(i + 1).padStart(2, '0')} · {r.sample ? 'Sample member' : r.id}</span><span className="mono">{r.recency} days · {inr(r.ratio)}</span></div>)}</div>
      <AnchorLink className="btn solid" href="/risk/" anchor="at-risk">Open the full list</AnchorLink></div>,
  ];

  return (
    <>
      <section className="hero">
        <div className="wrap">
          <div className="hero-top"><TypeHeading />
            <div><p className="lede">StreakForge follows <b>{nf(m.N)} gym members</b> from signup to churn. The leak is not renewals. It is the <b>first seven days</b>, and the headline churn number is hiding how much of this is real.</p>
              <div className="ctl-row"><AnchorLink className="btn solid" href="/insights/">Read the five findings</AnchorLink><button className="btn" id="play" onClick={play}>Play the story</button></div></div></div>
        </div>
        <div className="wrap"><div className="field-wrap" id="fieldWrap">
          <canvas id="field" ref={cv} role="img" aria-label={`Field of ${nf(m.N)} dots, one per synthetic member, rearranged by each chapter below`} />
          <div className="field-hud" id="hud">{hud.map((v, i) => <div key={i}><div className="num hud-n" data-i={i}>{nf(v[0])}</div><div className="hud-l">{v[1]}</div></div>)}</div>
          <div className="legend" id="legend">{LEGENDS[scene].map((l) => <span key={l[1]}><i style={{ background: LEG[l[0]] }} />{l[1]}</span>)}</div>
          <div className="tip" id="ftip" ref={tip} />
        </div></div>
        <div className="wrap">
          <div className="stage" role="tablist" aria-label="Story chapters" ref={stage} onClick={() => clearTimeout(playT.current)} onKeyDown={onKey}>
            {TITLES.map((t, i) => <button key={t} role="tab" aria-selected={i === scene} data-i={i} onClick={() => setScene(i)}><span className="k">0{i + 1}</span><span className="t">{t}</span></button>)}
          </div>
          <div className="story" aria-live="polite"><div><h3 id="storyH">{heading}</h3><div id="storyB">{body[scene]}</div></div><div id="storyC">{ctl[scene]}</div></div>
        </div>
      </section>
    </>
  );
}
