import { useEffect, useLayoutEffect, useRef, useState } from 'react';

/** Width of a host element, re-measured 150 ms after resizes (like the prototype). */
export function useWidth<T extends HTMLElement>() {
  const ref = useRef<T>(null);
  const [w, setW] = useState(0);
  useLayoutEffect(() => { if (ref.current) setW(ref.current.clientWidth); }, []);
  useEffect(() => {
    let t: ReturnType<typeof setTimeout>;
    const f = () => { clearTimeout(t); t = setTimeout(() => ref.current && setW(ref.current.clientWidth), 150); };
    window.addEventListener('resize', f);
    return () => { window.removeEventListener('resize', f); clearTimeout(t); };
  }, []);
  return [ref, w] as const;
}
