"use client";

import { useEffect, useRef } from "react";

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
}

/**
 * Animated constellation background: drifting particles on a near-black
 * canvas, linked by faint emerald/violet lines. Runs at the device frame
 * rate via requestAnimationFrame and respects prefers-reduced-motion.
 */
export function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);
    let raf = 0;

    const count = Math.min(90, Math.floor((width * height) / 18000));
    const particles: Particle[] = Array.from({ length: count }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      r: Math.random() * 1.6 + 0.4,
    }));

    const mouse = { x: -1000, y: -1000 };
    const onMove = (e: MouseEvent) => {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    };
    window.addEventListener("mousemove", onMove);

    const onResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener("resize", onResize);

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      // Soft radial aura (emerald + violet)
      const aura = ctx.createRadialGradient(
        width * 0.25, height * 0.3, 0,
        width * 0.25, height * 0.3, Math.max(width, height) * 0.6,
      );
      aura.addColorStop(0, "rgba(16,185,129,0.06)");
      aura.addColorStop(1, "rgba(16,185,129,0)");
      ctx.fillStyle = aura;
      ctx.fillRect(0, 0, width, height);

      const aura2 = ctx.createRadialGradient(
        width * 0.8, height * 0.15, 0,
        width * 0.8, height * 0.15, Math.max(width, height) * 0.55,
      );
      aura2.addColorStop(0, "rgba(139,92,246,0.05)");
      aura2.addColorStop(1, "rgba(139,92,246,0)");
      ctx.fillStyle = aura2;
      ctx.fillRect(0, 0, width, height);

      for (const p of particles) {
        if (!reduced) {
          p.x += p.vx;
          p.y += p.vy;
          if (p.x < 0 || p.x > width) p.vx *= -1;
          if (p.y < 0 || p.y > height) p.vy *= -1;
        }
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(226,232,240,0.5)";
        ctx.fill();
      }

      // Link nearby particles + react to cursor
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const a = particles[i];
          const b = particles[j];
          const dx = a.x - b.x;
          const dy = a.y - b.y;
          const dist = Math.hypot(dx, dy);
          if (dist < 120) {
            ctx.strokeStyle = `rgba(16,185,129,${0.12 * (1 - dist / 120)})`;
            ctx.lineWidth = 0.6;
            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
        const a = particles[i];
        const mdx = a.x - mouse.x;
        const mdy = a.y - mouse.y;
        const mdist = Math.hypot(mdx, mdy);
        if (mdist < 200) {
          const t = 1 - mdist / 200;
          // Brighter violet line that follows the cursor.
          ctx.strokeStyle = `rgba(167,139,250,${0.6 * t})`;
          ctx.lineWidth = 1.3;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(mouse.x, mouse.y);
          ctx.stroke();
          // Highlight the linked node so the "web" reads more clearly.
          ctx.beginPath();
          ctx.arc(a.x, a.y, a.r + 1.1 * t, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(196,181,253,${0.7 * t})`;
          ctx.fill();
        }
      }

      raf = requestAnimationFrame(draw);
    };
    draw();

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className="pointer-events-none fixed inset-0 -z-10 h-full w-full"
    />
  );
}
