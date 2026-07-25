"use client";

import { useEffect, useRef } from "react";

type Dot = {
  baseX: number;
  baseY: number;
  r: number;
  currentColor: { r: number; g: number; b: number };
};

const SPACING = 24;
const DEFAULT_RADIUS = 1;
const MAX_RADIUS = 3;
const HOVER_DISTANCE = 150;
const BASE_COLOR = { r: 209, g: 213, b: 219 }; // #d1d5db light grey
const GLOW_COLOR = { r: 0, g: 170, b: 255 }; // vibrant light blue

/**
 * Interactive grey-dot backdrop from stitch/code.html.
 * Near the cursor, dots enlarge and lighten to cyan/light-blue.
 */
export function DotCanvas() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dots: Dot[] = [];
    let mouse = { x: -1000, y: -1000 };
    let raf = 0;

    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    function initCanvas() {
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas!.width = Math.floor(width * dpr);
      canvas!.height = Math.floor(height * dpr);
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);

      dots = [];
      for (let x = 0; x < width; x += SPACING) {
        for (let y = 0; y < height; y += SPACING) {
          dots.push({
            baseX: x,
            baseY: y,
            r: DEFAULT_RADIUS,
            currentColor: { ...BASE_COLOR },
          });
        }
      }
    }

    function draw() {
      ctx!.clearRect(0, 0, width, height);

      for (const dot of dots) {
        const dx = mouse.x - dot.baseX;
        const dy = mouse.y - dot.baseY;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let targetR = DEFAULT_RADIUS;
        let targetColor = BASE_COLOR;

        if (!reduced && dist < HOVER_DISTANCE) {
          const factor = 1 - dist / HOVER_DISTANCE;
          targetR = DEFAULT_RADIUS + (MAX_RADIUS - DEFAULT_RADIUS) * factor;
          // Blend grey → light blue by proximity (stronger near cursor)
          targetColor = {
            r: Math.round(BASE_COLOR.r + (GLOW_COLOR.r - BASE_COLOR.r) * factor),
            g: Math.round(BASE_COLOR.g + (GLOW_COLOR.g - BASE_COLOR.g) * factor),
            b: Math.round(BASE_COLOR.b + (GLOW_COLOR.b - BASE_COLOR.b) * factor),
          };
        }

        const ease = reduced ? 1 : 0.15;
        dot.r += (targetR - dot.r) * ease;
        dot.currentColor.r += (targetColor.r - dot.currentColor.r) * ease;
        dot.currentColor.g += (targetColor.g - dot.currentColor.g) * ease;
        dot.currentColor.b += (targetColor.b - dot.currentColor.b) * ease;

        ctx!.beginPath();
        ctx!.arc(dot.baseX, dot.baseY, dot.r, 0, Math.PI * 2);
        ctx!.fillStyle = `rgb(${Math.round(dot.currentColor.r)}, ${Math.round(dot.currentColor.g)}, ${Math.round(dot.currentColor.b)})`;
        ctx!.fill();
      }

      raf = requestAnimationFrame(draw);
    }

    const onMove = (e: MouseEvent) => {
      mouse = { x: e.clientX, y: e.clientY };
    };
    const onLeave = () => {
      mouse = { x: -1000, y: -1000 };
    };

    initCanvas();
    draw();
    window.addEventListener("resize", initCanvas);
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseout", onLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", initCanvas);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseout", onLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      id="dotCanvas"
      className="pointer-events-none fixed inset-0 z-0"
      aria-hidden
    />
  );
}
