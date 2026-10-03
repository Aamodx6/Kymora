import React, { useEffect, useRef } from 'react';

interface RowTypeProps {
  text?: string;
  tag?: 'h1' | 'h2' | 'h3' | 'p' | 'div';
  minSize?: number;
  fluid?: number;
  maxSize?: number;
  stretch?: number;
  weight?: number;
  tracking?: number;
  lineHeight?: number;
  wordSpacing?: number;
  color?: string;
  marker?: string;
  paper?: string;
  trigger?: 'load' | 'scroll';
  effect?: boolean;
  walk?: boolean;
  className?: string;
  style?: React.CSSProperties;
}

interface Rect {
  x: number;
  y: number;
  w: number;
  h: number;
}

interface Segment {
  k: number;
  yc: number;
  x0: number;
  x1: number;
  d: number;
}

interface LineInfo {
  base: number;
  x0: number;
  x1: number;
  top: number;
  bot: number;
}

interface WordInfo {
  x0: number;
  x1: number;
  base: number;
  line: number;
}

interface SelectionRange {
  l0: number;
  l1: number;
  c0: number;
  c1: number;
}

const clamp = (val: number, min: number, max: number) =>
  Math.min(max, Math.max(min, val));

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
const easeOutQuart = (t: number) => 1 - Math.pow(1 - t, 4);

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const pseudoHash = (seed: number) => {
  const t = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return t - Math.floor(t);
};

export const RowType: React.FC<RowTypeProps> = ({
  text = 'Ask your data.\nExtract every feature.',
  tag: Tag = 'h1',
  minSize = 48,
  fluid = 6.3,
  maxSize = 88,
  stretch = 110,
  weight = 800,
  tracking = -0.035,
  lineHeight = 0.96,
  wordSpacing = 0,
  color = '#000000',
  marker = '#FFE53B',
  paper = '#F2F3EF',
  trigger = 'load',
  effect = true,
  walk = true,
  className = '',
  style = {},
}) => {
  const hostRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const host = hostRef.current;
    const textEl = textRef.current;
    const canvas = canvasRef.current;
    if (!host || !textEl || !canvas) return;

    let isDestroyed = false;
    let token = 0;
    let rafId = 0;
    let resizeTimer: number | null = null;
    const cleanups: (() => void)[] = [];

    // Font responsive sizing
    const updateFontSize = () => {
      const vw = window.innerWidth;
      const targetSize = clamp((fluid * vw) / 100, minSize, maxSize);
      textEl.style.fontSize = `${targetSize}px`;
    };

    updateFontSize();
    window.addEventListener('resize', updateFontSize);
    cleanups.push(() => window.removeEventListener('resize', updateFontSize));

    const reducedMotion =
      window.matchMedia('(prefers-reduced-motion: reduce)').matches || !effect;

    if (reducedMotion) {
      textEl.style.color = color;
      return () => {
        isDestroyed = true;
        cleanups.forEach((c) => c());
      };
    }

    textEl.style.color = 'transparent';
    const fallbackTimer = setTimeout(() => {
      if (!isDestroyed && textEl.style.color === 'transparent') {
        textEl.style.color = color;
      }
    }, 2500);
    cleanups.push(() => clearTimeout(fallbackTimer));

    // Internal animation engine
    class Engine {
      host: HTMLElement;
      text: HTMLElement;
      cv: HTMLCanvasElement;
      ctx: CanvasRenderingContext2D;
      mask: HTMLCanvasElement;
      mctx: CanvasRenderingContext2D;
      c: { ink: string; marker: string; paper: string };
      walkOn: boolean;
      pad = 28;
      sel: Rect | null = null;
      tw: { from: Rect; to: Rect; t0: number; dur: number } | null = null;
      g: SelectionRange | null = null;
      phase: 'wait' | 'build' | 'live' = 'wait';
      visible = false;
      t0 = 0;
      fs = 0;
      dpr = 1;
      W = 0;
      H = 0;
      lines: LineInfo[] = [];
      words: WordInfo[] = [];
      right = 0;
      colW = 0;
      maxCol = 0;
      P = 4;
      segments: Segment[] = [];

      constructor(
        hostEl: HTMLElement,
        textElement: HTMLElement,
        cvEl: HTMLCanvasElement,
        colors: { ink: string; marker: string; paper: string },
        walkAllowed: boolean
      ) {
        this.host = hostEl;
        this.text = textElement;
        this.cv = cvEl;
        this.ctx = cvEl.getContext('2d')!;
        this.mask = document.createElement('canvas');
        this.mctx = this.mask.getContext('2d', { willReadFrequently: true })!;
        this.c = colors;
        this.walkOn = walkAllowed;
        this.frame = this.frame.bind(this);
      }

      measure(): boolean {
        const textRect = this.text.getBoundingClientRect();
        const computed = getComputedStyle(this.text);
        const fontSize = parseFloat(computed.fontSize);
        const dpr = Math.min(window.devicePixelRatio || 1, 2);
        const pad = Math.round(clamp(fontSize * 0.3, 12, 28));
        const W = Math.ceil(textRect.width) + pad * 2;
        const H = Math.ceil(textRect.height) + pad * 2;

        this.fs = fontSize;
        this.dpr = dpr;
        this.pad = pad;
        this.W = W;
        this.H = H;

        for (const c of [this.cv, this.mask]) {
          c.width = Math.round(W * dpr);
          c.height = Math.round(H * dpr);
        }

        Object.assign(this.cv.style, {
          width: `${W}px`,
          height: `${H}px`,
          left: `${-pad}px`,
          top: `${-pad}px`,
        });

        const mctx = this.mctx;
        mctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        mctx.clearRect(0, 0, W, H);

        mctx.font = `${computed.fontStyle} ${computed.fontWeight} ${fontSize}px ${computed.fontFamily}`;
        mctx.textBaseline = 'alphabetic';
        mctx.fillStyle = this.c.ink;

        const metrics = mctx.measureText('Hxg');
        const ascent = metrics.fontBoundingBoxAscent || fontSize * 0.8;
        const descent = metrics.fontBoundingBoxDescent || fontSize * 0.2;
        const capAscent = mctx.measureText('H').actualBoundingBoxAscent || fontSize * 0.7;

        const range = document.createRange();
        const walker = document.createTreeWalker(this.text, NodeFilter.SHOW_TEXT);
        const chars: { x: number; x1: number; base: number }[] = [];
        const words: WordInfo[] = [];
        let currWord: { x0: number; x1: number; base: number } | null = null;
        let node: Node | null;

        while ((node = walker.nextNode())) {
          const content = node.textContent || '';
          for (let i = 0; i < content.length; i++) {
            const ch = content[i];
            if (/\s/.test(ch)) {
              currWord = null;
              continue;
            }
            range.setStart(node, i);
            range.setEnd(node, i + 1);
            const clientRect = range.getClientRects()[0];
            if (!clientRect || !clientRect.width) continue;

            const x = clientRect.left - textRect.left + pad;
            const y = clientRect.top - textRect.top + pad + (clientRect.height - (ascent + descent)) / 2 + ascent;

            mctx.fillText(ch, x, y);
            chars.push({ x, x1: x + clientRect.width, base: y });

            if (!currWord || Math.abs(currWord.base - y) > 1) {
              currWord = { x0: x, x1: x + clientRect.width, base: y };
              words.push({ ...currWord, line: 0 });
            } else {
              currWord.x1 = x + clientRect.width;
            }
          }
          currWord = null;
        }

        const lines: LineInfo[] = [];
        for (const ch of chars) {
          let line = lines.find((l) => Math.abs(l.base - ch.base) < fontSize * 0.3);
          if (!line) {
            line = { base: ch.base, x0: ch.x, x1: ch.x1, top: 0, bot: 0 };
            lines.push(line);
          }
          line.x0 = Math.min(line.x0, ch.x);
          line.x1 = Math.max(line.x1, ch.x1);
        }

        lines.sort((a, b) => a.base - b.base);
        for (const l of lines) {
          l.top = l.base - capAscent - fontSize * 0.12;
          l.bot = l.base + fontSize * 0.2;
        }

        for (const w of words) {
          w.line = lines.findIndex((l) => Math.abs(l.base - w.base) < fontSize * 0.3);
        }

        this.lines = lines;
        this.words = words;
        if (!lines.length) return false;

        this.right = Math.max(...lines.map((l) => l.x1)) + fontSize * 0.12;
        this.colW = Math.round(fontSize * 0.5);
        this.maxCol = Math.ceil((Math.max(...lines.map((l) => l.x1)) - pad) / this.colW);
        this.P = Math.max(3.5, fontSize * 0.08);

        this.segments = this.slice();
        const totalW = Math.max(1, W - pad * 2);
        for (const s of this.segments) {
          s.d =
            0.6 * clamp((s.x0 - pad) / totalW, 0, 1) +
            0.04 * pseudoHash(s.k * 13.7 + s.x0);
        }
        return true;
      }

      slice(): Segment[] {
        const { dpr, P, H } = this;
        const w = this.mask.width;
        const h = this.mask.height;
        const imgData = this.mctx.getImageData(0, 0, w, h).data;
        const segments: Segment[] = [];
        const rows = Math.floor(H / P);

        for (let r = 0; r < rows; r++) {
          const yc = (r + 0.5) * P;
          const pixelY = Math.min(h - 1, Math.floor(yc * dpr));
          const rowStart = pixelY * w * 4 + 3;
          let prevAlpha = 0;
          let startX = -1;

          for (let x = 0; x <= w; x++) {
            const alpha = x < w ? imgData[rowStart + x * 4] : 0;
            if (startX < 0 && alpha >= 128) {
              startX = x - 1 + (128 - prevAlpha) / Math.max(1, alpha - prevAlpha) + 0.5;
            } else if (startX >= 0 && alpha < 128) {
              const endX = x - 1 + (prevAlpha - 128) / Math.max(1, prevAlpha - alpha) + 0.5;
              segments.push({
                k: r,
                yc,
                x0: startX / dpr,
                x1: endX / dpr,
                d: 0,
              });
              startX = -1;
            }
            prevAlpha = alpha;
          }
        }
        return segments;
      }

      col(x: number, direction: number): number {
        const c = (x - this.pad) / this.colW;
        return direction < 0 ? Math.floor(c - 0.15) : Math.ceil(c + 0.15);
      }

      fit(range: SelectionRange): SelectionRange {
        const span = range.c1 - range.c0;
        let c0 = clamp(range.c0, 0, this.maxCol - 1);
        const c1 = clamp(c0 + span, c0 + 1, this.maxCol);
        c0 = Math.max(0, c1 - span);
        return {
          l0: clamp(range.l0, 0, this.lines.length - 1),
          l1: clamp(range.l1, 0, this.lines.length - 1),
          c0,
          c1,
        };
      }

      rectOf(sel: SelectionRange): Rect {
        const x = this.pad + sel.c0 * this.colW;
        const w = Math.min((sel.c1 - sel.c0) * this.colW, this.right - x);
        const y = this.lines[sel.l0].top;
        const h = this.lines[sel.l1].bot - y;
        return { x, y, w, h };
      }

      home(): SelectionRange {
        const lineIdx = 0;
        const lineWords = this.words.filter((w) => w.line === lineIdx);
        const first = lineWords[1] || lineWords[0];
        const last = lineWords[lineWords.length - 1] || first;
        return this.fit({
          l0: lineIdx,
          l1: lineIdx,
          c0: this.col(first ? first.x0 : 0, -1),
          c1: this.col(last ? last.x1 : this.right, 1),
        });
      }

      draw(time: number) {
        const { ctx, dpr, W, H } = this;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.clearRect(0, 0, W, H);

        if (this.phase === 'wait') return;
        if (this.phase === 'build') {
          this.drawBuild(time);
          return;
        }

        const sel = this.sel;
        ctx.save();
        if (sel && sel.w > 0.5) {
          ctx.beginPath();
          ctx.rect(0, 0, W, H);
          ctx.rect(sel.x, sel.y, sel.w, sel.h);
          ctx.clip('evenodd');
        }
        ctx.drawImage(this.mask, 0, 0, W, H);
        ctx.restore();

        if (sel && sel.w > 0.5) {
          this.drawSel(sel);
        }
      }

      drawSel(sel: Rect) {
        const { ctx, P } = this;
        // Marker yellow background
        ctx.fillStyle = this.c.marker;
        ctx.fillRect(sel.x, sel.y, sel.w, sel.h);

        // Clip text inside yellow highlight to draw horizontal raster scanlines
        ctx.save();
        ctx.beginPath();
        ctx.rect(sel.x, sel.y, sel.w, sel.h);
        ctx.clip();

        ctx.fillStyle = this.c.ink;
        const barHeight = P * 0.46;
        for (const seg of this.segments) {
          if (
            seg.yc < sel.y - P ||
            seg.yc > sel.y + sel.h + P ||
            seg.x1 < sel.x ||
            seg.x0 > sel.x + sel.w
          ) {
            continue;
          }
          ctx.fillRect(seg.x0, seg.yc - barHeight / 2, seg.x1 - seg.x0, barHeight);
        }
        ctx.restore();

        // 2px ink stroke around the highlight box
        ctx.strokeStyle = this.c.ink;
        ctx.lineWidth = 2;
        ctx.strokeRect(sel.x - 1, sel.y - 1, sel.w + 2, sel.h + 2);

        // Corner anchor dot at bottom right
        const dotSize = this.fs < 60 ? 7 : 9;
        const dotX = sel.x + sel.w - dotSize / 2 + 1;
        const dotY = sel.y + sel.h - dotSize / 2 + 1;

        ctx.fillStyle = this.c.paper;
        ctx.fillRect(dotX - 2, dotY - 2, dotSize + 4, dotSize + 4);
        ctx.fillStyle = this.c.ink;
        ctx.fillRect(dotX, dotY, dotSize, dotSize);
      }

      drawBuild(time: number) {
        const { ctx, P } = this;
        const elapsed = time - this.t0;
        const totalDuration = 1100;
        const progress = elapsed / totalDuration;
        const expandFactor = clamp((elapsed - totalDuration + 120) / 320, 0, 1);
        const barHeight = P * lerp(0.46, 1.04, easeOutCubic(expandFactor));
        const resolveAlpha = clamp((elapsed - totalDuration - 320 + 200) / 200, 0, 1);

        ctx.fillStyle = this.c.ink;
        ctx.globalAlpha = 1 - resolveAlpha;

        for (const seg of this.segments) {
          const segProgress = clamp((progress - seg.d) / 0.36, 0, 1);
          if (segProgress <= 0) continue;
          ctx.fillRect(
            seg.x0,
            seg.yc - barHeight / 2,
            (seg.x1 - seg.x0) * easeOutCubic(segProgress),
            barHeight
          );
        }

        if (resolveAlpha > 0) {
          ctx.globalAlpha = resolveAlpha;
          ctx.drawImage(this.mask, 0, 0, this.W, this.H);
        }
        ctx.globalAlpha = 1;

        if (elapsed >= 1480) {
          this.phase = 'live';
          setTimeout(() => {
            if (this.visible) this.startIdle();
          }, 260);
        }
      }

      tweenTo(target: Rect, duration: number) {
        this.tw = {
          from: this.sel && this.sel.w > 0.5 ? { ...this.sel } : { ...target, w: 0 },
          to: target,
          t0: performance.now(),
          dur: duration,
        };
        this.kick();
      }

      kick() {
        if (!rafId && !isDestroyed) {
          rafId = requestAnimationFrame(this.frame);
        }
      }

      frame(time: number) {
        rafId = 0;
        let continueAnimating = this.phase === 'build';
        if (this.tw) {
          const progress = clamp((time - this.tw.t0) / this.tw.dur, 0, 1);
          const eased = easeOutQuart(progress);
          const from = this.tw.from;
          const to = this.tw.to;

          this.sel = {
            x: lerp(from.x, to.x, eased),
            y: lerp(from.y, to.y, eased),
            w: lerp(from.w, to.w, eased),
            h: lerp(from.h, to.h, eased),
          };

          if (progress >= 1) {
            this.tw = null;
          } else {
            continueAnimating = true;
          }
        }

        this.draw(time);
        if (continueAnimating) this.kick();
      }

      *walkSteps(from: SelectionRange, to: SelectionRange) {
        const curr = { ...from };
        let safety = 80;
        while (
          safety-- > 0 &&
          (curr.l0 !== to.l0 || curr.l1 !== to.l1 || curr.c0 !== to.c0 || curr.c1 !== to.c1)
        ) {
          if (curr.l0 !== to.l0 || curr.l1 !== to.l1) {
            if (curr.l0 === curr.l1 && to.l0 === to.l1) {
              const dir = Math.sign(to.l0 - curr.l0);
              curr.l0 += dir;
              curr.l1 += dir;
            } else if (curr.l0 === to.l0) {
              curr.l1 += Math.sign(to.l1 - curr.l1);
            } else {
              curr.l0 += Math.sign(to.l0 - curr.l0);
            }
          } else {
            const currSpan = curr.c1 - curr.c0;
            const toSpan = to.c1 - to.c0;
            if (currSpan === toSpan) {
              const dir = Math.sign(to.c0 - curr.c0);
              curr.c0 += dir;
              curr.c1 += dir;
            } else if (currSpan > toSpan) {
              if (Math.abs(curr.c1 - to.c1) >= Math.abs(curr.c0 - to.c0)) {
                curr.c1 -= 1;
              } else {
                curr.c0 += 1;
              }
            } else {
              if (Math.abs(curr.c1 - to.c1) >= Math.abs(curr.c0 - to.c0)) {
                curr.c1 += 1;
              } else {
                curr.c0 -= 1;
              }
            }
          }
          yield { ...curr };
        }
      }

      async startIdle() {
        if (this.phase !== 'live' || !this.walkOn || isDestroyed) return;
        const currentToken = ++token;
        const homeRange = this.home();
        const lineWords = this.words.filter((w) => w.line === homeRange.l0);
        const secondToLast = lineWords[Math.max(0, lineWords.length - 2)];
        const subCol = this.col(secondToLast ? secondToLast.x1 : this.right, 1);
        const prevLine = Math.max(0, homeRange.l0 - 1);

        const rawSequence: [SelectionRange, number][] = [
          [homeRange, 2600],
          [{ ...homeRange, c1: subCol }, 700],
          [{ l0: prevLine, l1: prevLine, c0: homeRange.c0, c1: subCol }, 800],
          [{ l0: prevLine, l1: prevLine, c0: homeRange.c0 - 3, c1: subCol - 3 }, 700],
          [{ l0: prevLine, l1: homeRange.l1, c0: homeRange.c0 - 3, c1: subCol - 3 }, 1000],
          [{ l0: homeRange.l0, l1: homeRange.l1, c0: 0, c1: 4 }, 800],
        ];

        const sequence: [SelectionRange, number][] = rawSequence.map(
          ([range, delay]): [SelectionRange, number] => [this.fit(range), delay]
        );

        if (!this.g) {
          this.g = sequence[0][0];
          this.tweenTo(this.rectOf(this.g), 380);
          await sleep(380);
        }

        while (currentToken === token && !isDestroyed) {
          for (const [targetRange, holdTime] of sequence) {
            for (const step of this.walkSteps(this.g, targetRange)) {
              if (currentToken !== token) return;
              this.g = step;
              this.tweenTo(this.rectOf(step), 90);
              await sleep(125);
            }
            if (currentToken !== token) return;
            await sleep(holdTime);
            if (currentToken !== token) return;
          }
        }
      }

      bindPointer() {
        let idleTimer: number | null = null;

        const onPointerMove = (e: PointerEvent) => {
          if (this.phase !== 'live' || !this.g || e.pointerType === 'touch') return;
          const rect = this.cv.getBoundingClientRect();
          const mouseX = e.clientX - rect.left;
          const mouseY = e.clientY - rect.top;

          const lineIdx = this.lines.findIndex(
            (l) => mouseY >= l.top - 8 && mouseY <= l.bot + 8
          );
          if (lineIdx < 0) return;

          const col = Math.floor((mouseX - this.pad) / this.colW);
          const targetRange = this.fit({
            l0: lineIdx,
            l1: lineIdx,
            c0: col - 2,
            c1: col + 2,
          });

          token++;
          if (idleTimer) clearTimeout(idleTimer);

          if (
            targetRange.l0 !== this.g.l0 ||
            targetRange.l1 !== this.g.l1 ||
            targetRange.c0 !== this.g.c0 ||
            targetRange.c1 !== this.g.c1
          ) {
            this.g = targetRange;
            this.tweenTo(this.rectOf(targetRange), 120);
          }

          idleTimer = window.setTimeout(() => this.startIdle(), 2400);
        };

        const onPointerLeave = () => {
          if (idleTimer) clearTimeout(idleTimer);
          idleTimer = window.setTimeout(() => this.startIdle(), 900);
        };

        this.host.addEventListener('pointermove', onPointerMove);
        this.host.addEventListener('pointerleave', onPointerLeave);

        cleanups.push(() => {
          if (idleTimer) clearTimeout(idleTimer);
          this.host.removeEventListener('pointermove', onPointerMove);
          this.host.removeEventListener('pointerleave', onPointerLeave);
        });
      }

      settle() {
        this.phase = 'live';
        this.g = this.home();
        this.sel = this.rectOf(this.g);
        this.draw(performance.now());
      }

      start(interactive: boolean, startTrigger: 'load' | 'scroll'): boolean {
        if (!this.measure()) return false;
        this.host.setAttribute('data-live', '');

        if (interactive) {
          if (startTrigger === 'load') {
            this.phase = 'build';
            this.t0 = performance.now();
            this.kick();
          } else {
            this.draw(performance.now());
          }
        } else {
          this.settle();
        }

        const observer = new IntersectionObserver(
          (entries) => {
            entries.forEach((entry) => {
              this.visible = entry.isIntersecting;
              if (interactive) {
                if (entry.isIntersecting) {
                  if (this.phase === 'wait' && entry.intersectionRatio > 0.3) {
                    this.phase = 'build';
                    this.t0 = performance.now();
                    this.kick();
                  } else if (this.phase === 'live') {
                    this.startIdle();
                  }
                } else {
                  token++;
                }
              }
            });
          },
          { threshold: [0, 0.35] }
        );

        observer.observe(this.host);
        cleanups.push(() => observer.disconnect());

        if (interactive) {
          this.bindPointer();
        }

        let lastWidth = this.host.offsetWidth;
        const resizeObserver = new ResizeObserver(() => {
          if (resizeTimer) clearTimeout(resizeTimer);
          resizeTimer = window.setTimeout(() => {
            if (isDestroyed || !this.measure()) return;
            if (this.g) {
              this.g = this.fit(this.g);
              this.sel = this.rectOf(this.g);
            } else if (this.phase === 'live') {
              this.settle();
            }
            this.draw(performance.now());

            const newWidth = this.host.offsetWidth;
            if (newWidth !== lastWidth) {
              lastWidth = newWidth;
              if (this.phase === 'live' && interactive && this.visible) {
                this.g = null;
                this.sel = null;
                this.startIdle();
              }
            }
          }, 140);
        });

        resizeObserver.observe(this.host);
        cleanups.push(() => {
          if (resizeTimer) clearTimeout(resizeTimer);
          resizeObserver.disconnect();
        });

        return true;
      }
    }

    // Wait for fonts to be ready before measuring
    document.fonts.ready.then(() => {
      if (isDestroyed) return;
      updateFontSize();
      const engine = new Engine(
        host,
        textEl,
        canvas,
        { ink: color, marker, paper },
        walk
      );

      if (!engine.start(!reducedMotion, trigger)) {
        textEl.style.color = color;
      }
    });

    return () => {
      isDestroyed = true;
      token++;
      if (rafId) cancelAnimationFrame(rafId);
      cleanups.forEach((c) => c());
    };
  }, [
    text,
    minSize,
    fluid,
    maxSize,
    stretch,
    weight,
    tracking,
    lineHeight,
    wordSpacing,
    color,
    marker,
    paper,
    trigger,
    effect,
    walk,
  ]);

  const textLines = (text || '').split(/\n|\\n/);

  return (
    <div
      ref={hostRef}
      data-rowtype=""
      className={`relative select-none ${className}`}
      style={{ position: 'relative', ...style }}
    >
      <Tag
        ref={textRef as any}
        data-rowtype-text=""
        style={{
          margin: 0,
          fontFamily:
            '"Archivo", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif',
          fontWeight: weight,
          fontStretch: `${stretch}%`,
          lineHeight,
          letterSpacing: `${tracking}em`,
          wordSpacing: wordSpacing ? `${wordSpacing}em` : undefined,
          fontVariantLigatures: 'none',
          color: effect ? 'transparent' : color,
          animation: effect ? 'logitRowTypeShow 0s linear 1.4s forwards' : undefined,
        }}
      >
        {textLines.map((line, i) => (
          <React.Fragment key={i}>
            {i > 0 && <br />}
            {line}
          </React.Fragment>
        ))}
      </Tag>

      <canvas
        ref={canvasRef}
        aria-hidden="true"
        className="pointer-events-none absolute"
        style={{ position: 'absolute', pointerEvents: 'none' }}
      />
    </div>
  );
};

export default RowType;
