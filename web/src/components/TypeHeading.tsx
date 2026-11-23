'use client';
import { useEffect } from 'react';

/* Plays once per page load (module flag), not when the visitor returns to Overview via the nav. */
let played = false;
const STEP = 50; // ms per character

/** Hero heading: full text is always in the DOM (layout reserved, screen readers and copy/paste read it all);
    characters are revealed one by one by CSS, with a cursor that follows the typing position. */
export function TypeHeading() {
  useEffect(() => { played = true; }, []);
  const parts: [string, boolean][] = [['81 in 100 members never show up in ', false], ['week one.', true]];
  let i = 0;
  const word = (w: string, k: string) => (
    <span key={k}>{Array.from(w).map((ch) => { const n = i++; return <span key={n} className="c" style={{ ['--d' as string]: `${n * STEP}ms` }} data-last={n === 43 ? '' : undefined}>{ch}</span>; })}</span>
  );
  const render = (text: string, k: string) => text.split(/(\s+)/).map((t, j) => (/^\s+$/.test(t) ? (() => { i += t.length; return t; })() : t ? word(t, `${k}${j}`) : null));
  return (
    <h1 className={'tw' + (played ? ' done' : '')}>
      {render(parts[0][0], 'a')}<em>{render(parts[1][0], 'b')}</em>
    </h1>
  );
}
