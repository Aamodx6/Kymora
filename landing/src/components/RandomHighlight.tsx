import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { motion } from 'framer-motion';

export interface RandomHighlightProps {
  words?: string[];
  text?: string;
  lines?: string[]; // Multi-line headline support
  intervalRange?: [number, number]; // [minMs, maxMs], default [2000, 2800]
  color?: string; // default "#FFE53B"
  maxSpan?: number;
  staticSpan?: number;
  className?: string;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span';
  staticWordIndex?: number;
  dotHandle?: boolean;
  scanlines?: boolean;
  enableHover?: boolean;
  hoverBoxWidth?: number; // Width of the compact box following cursor, default 175px
}

interface BoxCoords {
  x: number;
  y: number;
  width: number;
  height: number;
  rotate: number;
  visible: boolean;
}

export const RandomHighlight: React.FC<RandomHighlightProps> = ({
  words: wordsProp,
  text,
  lines,
  intervalRange = [2000, 2800],
  color = '#FFE53B',
  className = '',
  as: Component = 'span',
  staticWordIndex,
  dotHandle = true,
  scanlines = true,
  enableHover = true,
  hoverBoxWidth = 175,
}) => {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const wordRefs = useRef<(HTMLSpanElement | null)[]>([]);
  const timerRef = useRef<number | null>(null);
  const isHoveredRef = useRef(false);
  const currentTargetRef = useRef<{ start: number; span: number }>({ start: 0, span: 1 });

  // Parse words list and line breaks
  const wordsList = useMemo(() => {
    if (wordsProp && wordsProp.length > 0) return wordsProp;
    if (lines && lines.length > 0) {
      return lines.flatMap((line) => line.trim().split(/\s+/));
    }
    if (text) return text.trim().split(/\s+/);
    return [];
  }, [wordsProp, lines, text]);

  // Reduced motion preference
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    setReducedMotion(mq.matches);

    const onChange = (e: MediaQueryListEvent) => setReducedMotion(e.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const [boxState, setBoxState] = useState<BoxCoords>({
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    rotate: 0,
    visible: false,
  });

  const [parentDim, setParentDim] = useState({ width: 0, height: 0 });

  // Measure word-based target for autonomous jumps
  const measureTarget = useCallback(
    (startIdx: number, spanCount: number) => {
      if (!containerRef.current || wordsList.length === 0) return;

      const parentRect = containerRef.current.getBoundingClientRect();
      setParentDim({ width: parentRect.width, height: parentRect.height });

      const firstEl = wordRefs.current[startIdx];
      if (!firstEl) return;

      const firstRect = firstEl.getBoundingClientRect();
      const maxEnd = Math.min(startIdx + spanCount - 1, wordsList.length - 1);

      let validEndIdx = startIdx;
      for (let i = startIdx + 1; i <= maxEnd; i++) {
        const el = wordRefs.current[i];
        if (!el) break;
        const rect = el.getBoundingClientRect();
        if (Math.abs(rect.top - firstRect.top) > 14) break;
        validEndIdx = i;
      }

      const lastEl = wordRefs.current[validEndIdx] || firstEl;
      const lastRect = lastEl.getBoundingClientRect();

      const paddingX = 6;
      const paddingY = 4;

      const x = firstRect.left - parentRect.left - paddingX;
      const y = firstRect.top - parentRect.top - paddingY;
      const width = lastRect.right - firstRect.left + paddingX * 2;
      const height = firstRect.height + paddingY * 2;

      setBoxState({
        x,
        y,
        width,
        height,
        rotate: 0,
        visible: true,
      });

      currentTargetRef.current = { start: startIdx, span: validEndIdx - startIdx + 1 };
    },
    [wordsList.length]
  );

  // Autonomous jump loop
  const jumpNext = useCallback(() => {
    if (wordsList.length === 0 || isHoveredRef.current) return;

    const current = currentTargetRef.current;
    let nextStart = current.start;
    let attempts = 0;

    while (attempts < 12) {
      nextStart = Math.floor(Math.random() * wordsList.length);
      if (nextStart !== current.start || wordsList.length <= 1) {
        break;
      }
      attempts++;
    }

    measureTarget(nextStart, 1);

    const [minTime, maxTime] = intervalRange;
    const nextInterval = Math.floor(Math.random() * (maxTime - minTime + 1)) + minTime;
    timerRef.current = window.setTimeout(jumpNext, nextInterval);
  }, [wordsList.length, intervalRange, measureTarget]);

  // Real-time mouse hover tracking: small compact box around the cursor
  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!enableHover || !containerRef.current) return;
    isHoveredRef.current = true;
    if (timerRef.current) clearTimeout(timerRef.current);

    const parentRect = containerRef.current.getBoundingClientRect();
    setParentDim({ width: parentRect.width, height: parentRect.height });

    const mouseX = e.clientX - parentRect.left;
    const mouseY = e.clientY - parentRect.top;

    // Small compact area box around cursor (as requested and shown in screenshot)
    const boxW = hoverBoxWidth;

    // Determine the line the cursor is closest to
    let closestLineY = 0;
    let closestLineHeight = 80;
    let minDistanceY = Infinity;

    for (let i = 0; i < wordsList.length; i++) {
      const el = wordRefs.current[i];
      if (!el) continue;
      const r = el.getBoundingClientRect();
      const elY = r.top - parentRect.top;
      const dist = Math.abs(mouseY - (elY + r.height / 2));
      if (dist < minDistanceY) {
        minDistanceY = dist;
        closestLineY = elY - 4;
        closestLineHeight = r.height + 8;
      }
    }

    // Center box horizontally on mouse cursor
    const targetX = Math.max(-10, Math.min(parentRect.width - boxW + 10, mouseX - boxW / 2));

    setBoxState({
      x: targetX,
      y: closestLineY,
      width: boxW,
      height: closestLineHeight,
      rotate: 0,
      visible: true,
    });
  };

  const handlePointerLeave = () => {
    if (!enableHover) return;
    isHoveredRef.current = false;
    if (!reducedMotion) {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = window.setTimeout(jumpNext, 1600);
    }
  };

  // Main lifecycle
  useEffect(() => {
    if (wordsList.length === 0) return;

    const initialStart =
      staticWordIndex !== undefined
        ? Math.min(staticWordIndex, wordsList.length - 1)
        : Math.max(0, wordsList.length - 2);

    measureTarget(initialStart, 1);

    if (typeof document !== 'undefined' && 'fonts' in document) {
      document.fonts.ready.then(() => {
        const cur = currentTargetRef.current;
        measureTarget(cur.start, cur.span);
      });
    }

    const handleResize = () => {
      const cur = currentTargetRef.current;
      measureTarget(cur.start, cur.span);
    };
    window.addEventListener('resize', handleResize);

    const handleVisibility = () => {
      if (document.hidden) {
        if (timerRef.current) clearTimeout(timerRef.current);
      } else if (!reducedMotion && !isHoveredRef.current) {
        jumpNext();
      }
    };
    document.addEventListener('visibilitychange', handleVisibility);

    if (!reducedMotion) {
      const [minTime, maxTime] = intervalRange;
      const firstDelay = Math.floor(Math.random() * (maxTime - minTime + 1)) + minTime;
      timerRef.current = window.setTimeout(jumpNext, firstDelay);
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibility);
    };
  }, [wordsList, reducedMotion, intervalRange, measureTarget, jumpNext, staticWordIndex]);

  return (
    <Component
      ref={containerRef as any}
      onPointerMove={handlePointerMove}
      onPointerLeave={handlePointerLeave}
      className={`relative inline-block cursor-default select-none ${className}`}
      style={{ isolation: 'isolate' }}
    >
      {/* Moving Yellow Box with 1px border and corner dot */}
      <motion.div
        aria-hidden="true"
        initial={false}
        animate={{
          x: boxState.x,
          y: boxState.y,
          width: boxState.width,
          height: boxState.height,
          rotate: boxState.rotate,
          opacity: boxState.visible ? 1 : 0,
        }}
        transition={{
          duration: isHoveredRef.current ? 0.08 : 0.35,
          ease: isHoveredRef.current ? 'easeOut' : [0.22, 1, 0.36, 1],
        }}
        className="pointer-events-none absolute left-0 top-0 z-10 overflow-hidden"
        style={{
          backgroundColor: color,
          border: '1px solid #000000',
          borderRadius: '2px',
        }}
      >
        {/* Tiny black square anchor handle at bottom right */}
        {dotHandle && (
          <span
            className="absolute -bottom-0.5 -right-0.5 h-1.5 w-1.5 bg-black"
            aria-hidden="true"
          />
        )}

        {/* Text clone rendered with horizontal raster scanlines */}
        {scanlines && parentDim.width > 0 && (
          <div
            className="absolute pointer-events-none select-none"
            style={{
              left: -boxState.x - 1, // align border offset
              top: -boxState.y - 1,
              width: parentDim.width,
              height: parentDim.height,
            }}
          >
            <div className={`raster-scanlines text-ink ${className}`}>
              {lines && lines.length > 0 ? (
                lines.map((line, lIdx) => (
                  <React.Fragment key={lIdx}>
                    {line}
                    {lIdx < lines.length - 1 && <br />}
                  </React.Fragment>
                ))
              ) : (
                wordsList.map((word, wIdx) => (
                  <React.Fragment key={wIdx}>
                    <span>{word}</span>
                    {wIdx < wordsList.length - 1 && ' '}
                  </React.Fragment>
                ))
              )}
            </div>
          </div>
        )}
      </motion.div>

      {/* Base Solid Text Layer */}
      {lines && lines.length > 0 ? (
        lines.map((line, lIdx) => {
          const lineWords = line.trim().split(/\s+/);
          let offset = 0;
          for (let prev = 0; prev < lIdx; prev++) {
            offset += lines[prev].trim().split(/\s+/).length;
          }

          return (
            <React.Fragment key={lIdx}>
              {lineWords.map((word, wIdx) => {
                const globalIdx = offset + wIdx;
                return (
                  <React.Fragment key={wIdx}>
                    <span
                      ref={(el) => (wordRefs.current[globalIdx] = el)}
                      data-hl
                      className="relative z-0 inline-block transition-colors"
                    >
                      {word}
                    </span>
                    {wIdx < lineWords.length - 1 && ' '}
                  </React.Fragment>
                );
              })}
              {lIdx < lines.length - 1 && <br />}
            </React.Fragment>
          );
        })
      ) : (
        wordsList.map((word, idx) => (
          <React.Fragment key={idx}>
            <span
              ref={(el) => (wordRefs.current[idx] = el)}
              data-hl
              className="relative z-0 inline-block transition-colors"
            >
              {word}
            </span>
            {idx < wordsList.length - 1 && ' '}
          </React.Fragment>
        ))
      )}
    </Component>
  );
};
