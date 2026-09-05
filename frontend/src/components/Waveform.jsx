import { useEffect, useRef } from "react";

const BARS = 36;

/** Scrolling loudness bars drawn straight to a canvas (no React re-render per frame). */
export default function Waveform({ level, color = "#e0475c", active = true }) {
  const ref = useRef(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return undefined;
    const ctx = canvas.getContext("2d");
    const history = new Array(BARS).fill(0);
    let frame = 0;
    let last = 0;

    const draw = (now) => {
      frame = requestAnimationFrame(draw);
      if (now - last < 50) return; // ~20 fps is plenty for a meter
      last = now;
      history.push(Math.max(0.06, level?.() ?? 0));
      history.shift();

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.clientWidth;
      const h = canvas.clientHeight;
      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
        canvas.width = w * dpr;
        canvas.height = h * dpr;
      }
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);
      const gap = 3;
      const bw = Math.max(2, (w - gap * (BARS - 1)) / BARS);
      ctx.fillStyle = color;
      history.forEach((v, i) => {
        const bh = Math.max(3, v * h);
        const x = i * (bw + gap);
        const y = (h - bh) / 2;
        ctx.globalAlpha = 0.35 + (i / BARS) * 0.65; // newest bars brightest
        ctx.beginPath();
        ctx.roundRect(x, y, bw, bh, bw / 2);
        ctx.fill();
      });
      ctx.globalAlpha = 1;
    };

    if (active) frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, [level, color, active]);

  return <canvas ref={ref} className="wave" aria-hidden="true" />;
}
