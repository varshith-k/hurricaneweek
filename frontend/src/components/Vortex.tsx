"use client";

import { useEffect, useRef } from "react";
import { createNoise3D } from "simplex-noise";

interface Particle {
  x: number;
  y: number;
  angle: number;
  speed: number;
  radius: number;
  life: number;
  maxLife: number;
}

const PARTICLE_COUNT = 220;
const BASE_HUE = 168; // matches the app's teal/emerald accent (#5eead4)

export function Vortex({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const noise3D = createNoise3D();
    let width = 0;
    let height = 0;
    let centerX = 0;
    let centerY = 0;
    let animationFrame = 0;
    let time = 0;

    const particles: Particle[] = [];

    function resize() {
      const parent = canvas!.parentElement;
      width = parent ? parent.clientWidth : window.innerWidth;
      height = parent ? parent.clientHeight : window.innerHeight;
      canvas!.width = width * window.devicePixelRatio;
      canvas!.height = height * window.devicePixelRatio;
      canvas!.style.width = `${width}px`;
      canvas!.style.height = `${height}px`;
      ctx!.setTransform(window.devicePixelRatio, 0, 0, window.devicePixelRatio, 0, 0);
      centerX = width / 2;
      centerY = height / 2;
    }

    function spawnParticle(): Particle {
      const angle = Math.random() * Math.PI * 2;
      const radius = Math.random() * Math.min(width, height) * 0.45;
      return {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
        angle,
        speed: 0.004 + Math.random() * 0.006,
        radius,
        life: 0,
        maxLife: 120 + Math.random() * 160,
      };
    }

    resize();
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const p = spawnParticle();
      p.life = Math.random() * p.maxLife;
      particles.push(p);
    }

    function draw() {
      ctx!.fillStyle = "rgba(10, 17, 23, 0.28)";
      ctx!.fillRect(0, 0, width, height);

      for (const p of particles) {
        const noise = noise3D(p.x * 0.002, p.y * 0.002, time * 0.15);
        p.angle += p.speed + noise * 0.01;
        p.radius -= 0.35;
        if (p.radius < 12) {
          Object.assign(p, spawnParticle());
        }
        p.x = centerX + Math.cos(p.angle) * p.radius;
        p.y = centerY + Math.sin(p.angle) * p.radius;
        p.life += 1;

        const lifeRatio = p.life / p.maxLife;
        const fade = Math.sin(Math.PI * Math.min(lifeRatio, 1));
        const distanceRatio = 1 - p.radius / (Math.min(width, height) * 0.45);

        ctx!.beginPath();
        ctx!.fillStyle = `hsla(${BASE_HUE}, 85%, ${55 + distanceRatio * 20}%, ${0.15 + fade * 0.55})`;
        ctx!.arc(p.x, p.y, 1 + distanceRatio * 1.8, 0, Math.PI * 2);
        ctx!.fill();

        if (p.life > p.maxLife) {
          Object.assign(p, spawnParticle());
        }
      }

      time += 1;
      animationFrame = requestAnimationFrame(draw);
    }

    if (prefersReducedMotion) {
      // Draw a single static frame instead of animating.
      draw();
      cancelAnimationFrame(animationFrame);
    } else {
      draw();
    }

    window.addEventListener("resize", resize);
    return () => {
      cancelAnimationFrame(animationFrame);
      window.removeEventListener("resize", resize);
    };
  }, []);

  return <canvas ref={canvasRef} className={`pointer-events-none block ${className}`} aria-hidden="true" />;
}
