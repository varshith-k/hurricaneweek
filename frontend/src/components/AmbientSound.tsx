"use client";

import { useEffect, useRef, useState } from "react";

const STORAGE_KEY = "hurricane-week-ambient-enabled";

export function AmbientSound() {
  const audioRef = useRef<HTMLAudioElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setEnabled(window.localStorage.getItem(STORAGE_KEY) === "true");
    } catch {
      // ignore - default to off
    }
    setReady(true);
  }, []);

  useEffect(() => {
    if (!ready || !audioRef.current) return;
    if (enabled) {
      audioRef.current.volume = 0.25;
      void audioRef.current.play().catch(() => {
        // Autoplay can still be blocked until a user gesture; the toggle click itself counts as one.
      });
    } else {
      audioRef.current.pause();
    }
    try {
      window.localStorage.setItem(STORAGE_KEY, String(enabled));
    } catch {
      // ignore
    }
  }, [enabled, ready]);

  return (
    <>
      <audio ref={audioRef} loop preload="none" src={`${process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000/api"}/ambient-sound`} />
      <button
        type="button"
        onClick={() => setEnabled((value) => !value)}
        aria-pressed={enabled}
        aria-label={enabled ? "Mute storm ambience" : "Play storm ambience"}
        className="fixed bottom-4 right-4 z-40 flex items-center gap-2 rounded-full border border-border bg-surface/90 px-4 py-2 text-sm text-muted shadow-lg backdrop-blur-sm transition hover:border-accent hover:text-text"
      >
        <svg viewBox="0 0 24 24" className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M11 5 6 9H3v6h3l5 4V5Z" />
          {enabled ? (
            <path d="M16 8a5 5 0 0 1 0 8M19 5a9 9 0 0 1 0 14" />
          ) : (
            <path d="M17 9 23 15M23 9l-6 6" />
          )}
        </svg>
        Storm ambience
      </button>
    </>
  );
}
