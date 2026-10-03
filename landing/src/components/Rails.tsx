import React, { useEffect, useRef } from 'react';

interface RailsProps {
  contentWidth?: number;
  gutter?: number;
  density?: number;
  speed?: number;
  scrollFactor?: number;
  stretch?: number;
  ink?: string;
  marker?: string;
  effect?: boolean;
  className?: string;
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const pseudoRandom = (seed: number) => {
  const t = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return t - Math.floor(t);
};

export const Rails: React.FC<RailsProps> = ({
  contentWidth = 1200,
  gutter = 24,
  density = 0.58,
  speed = 0.008,
  scrollFactor = 0.35,
  stretch = 0.55,
  ink = '#000000',
  marker = '#FFE53B',
  effect = true,
  className = '',
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    const canvas = canvasRef.current;
    if (!container || !canvas || !effect) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const densityThreshold = 1 - density;
    let dpr = 1;
    let width = 0;
    let height = 0;
    let gutterWidth = 0;
    let scrollSpeed = 0;
    let lastScrollY: number | null = null;
    const startTime = performance.now();
    let rafId = 0;
    let isDestroyed = false;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = container.offsetWidth;
      height = container.offsetHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;

      const contentColumn = Math.min(contentWidth, width - gutter * 2);
      gutterWidth = (width - contentColumn) / 2 - 36;
    };

    const getRowSegment = (rowIdx: number, side: number) => {
      const slot = Math.floor(rowIdx / 26);
      const subRow = rowIdx - slot * 26;
      const offset = side ? 101 : 0;

      if (pseudoRandom(slot * 7.7 + offset) < densityThreshold) return null;

      const len = 4 + Math.floor(pseudoRandom(slot * 3.3 + offset + 17) * 6);
      const j = subRow - Math.floor(pseudoRandom(slot * 5.1 + offset + 29) * (26 - len));

      if (j < 0 || j >= len) return null;

      return {
        slot,
        j,
        len,
        kind: Math.floor(pseudoRandom(slot * 9.9 + offset + 3) * 3),
        offset,
      };
    };

    const render = (elapsedTime: number, currentScrollY: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);

      if (gutterWidth < 18) return;

      const stretchFactor = 1 + Math.min(stretch, scrollSpeed * 0.03);
      const scrollPos = elapsedTime * speed + currentScrollY * scrollFactor;
      const baseRow = Math.floor(scrollPos / 12);
      const rowOffset = scrollPos - baseRow * 12;
      const visibleRows = Math.ceil(height / 12) + 2;

      for (let r = -1; r < visibleRows; r++) {
        const rowIdx = baseRow + r;
        const yPos = r * 12 - rowOffset;

        for (let side = 0; side < 2; side++) {
          const seg = getRowSegment(rowIdx, side);
          if (!seg) continue;

          const progress = (seg.j + 0.5) / seg.len;
          const sigmoid = 1 / (1 + Math.exp(-(progress - 0.5) * 9));
          let shape =
            seg.kind === 0
              ? Math.sin(Math.PI * progress)
              : seg.kind === 1
              ? sigmoid
              : 1 - sigmoid;

          shape =
            (0.18 + 0.82 * shape) *
            (0.82 + 0.18 * pseudoRandom(rowIdx * 1.37 + seg.offset)) *
            (0.9 + 0.1 * Math.sin(elapsedTime * 0.0012 + rowIdx * 0.9 + seg.offset));

          const barWidth = Math.round(
            Math.min(1, shape * 0.8 * stretchFactor) * gutterWidth
          );

          // Marker color for center row of occasional slots
          const isMarker =
            pseudoRandom(seg.slot * 2.2 + seg.offset) > 0.55 &&
            seg.j === Math.floor(seg.len / 2);

          ctx.fillStyle = isMarker ? marker : ink;

          if (side === 0) {
            ctx.fillRect(0, yPos, barWidth, 6);
          } else {
            ctx.fillRect(width - barWidth, yPos, barWidth, 6);
          }
        }
      }
    };

    const animate = (timestamp: number) => {
      if (isDestroyed) return;
      const currentScrollY = window.scrollY;
      scrollSpeed = lerp(
        scrollSpeed,
        Math.abs(currentScrollY - (lastScrollY ?? currentScrollY)),
        0.12
      );
      lastScrollY = currentScrollY;

      render(timestamp - startTime + 40000, currentScrollY);

      if (document.visibilityState === 'visible') {
        rafId = requestAnimationFrame(animate);
      }
    };

    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    resize();
    const resizeObserver = new ResizeObserver(() => {
      resize();
      if (reducedMotion) {
        render(40000, window.scrollY);
      }
    });
    resizeObserver.observe(container);

    const onVisibilityChange = () => {
      if (!reducedMotion && !rafId && document.visibilityState === 'visible') {
        rafId = requestAnimationFrame(animate);
      }
    };

    if (reducedMotion) {
      render(40000, window.scrollY);
      const onScroll = () => render(40000, window.scrollY);
      window.addEventListener('scroll', onScroll, { passive: true });
      return () => {
        isDestroyed = true;
        resizeObserver.disconnect();
        window.removeEventListener('scroll', onScroll);
      };
    } else {
      rafId = requestAnimationFrame(animate);
      document.addEventListener('visibilitychange', onVisibilityChange);
      return () => {
        isDestroyed = true;
        if (rafId) cancelAnimationFrame(rafId);
        resizeObserver.disconnect();
        document.removeEventListener('visibilitychange', onVisibilityChange);
      };
    }
  }, [contentWidth, gutter, density, speed, scrollFactor, stretch, ink, marker, effect]);

  return (
    <div
      ref={containerRef}
      aria-hidden="true"
      className={`fixed inset-0 pointer-events-none z-0 overflow-hidden ${className}`}
    >
      {effect && (
        <canvas
          ref={canvasRef}
          className="absolute left-0 top-0 block"
        />
      )}
    </div>
  );
};

export default Rails;
