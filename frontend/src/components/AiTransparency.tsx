"use client";

import { useState } from "react";

const capabilities = [
  {
    feature: "Readiness Assistant",
    provider: "Snowflake Cortex (Gemini fallback)",
    shared: "Your question, retrieved FEMA/NOAA preparedness facts, your last run's outcome and gaps (no name)",
    purpose: "Answer hurricane-prep questions, grounded in real facts",
  },
  {
    feature: "AI Preparedness Coach",
    provider: "Google Gemini",
    shared: "Your decisions, scores, outcome, and preparedness gaps",
    purpose: "Explain what helped, what hurt, and one concrete change",
  },
  {
    feature: "Spoken debrief",
    provider: "ElevenLabs",
    shared: "Generated debrief text (outcome, score, strengths)",
    purpose: "Narrate your final report as audio",
  },
];

export function AiTransparencyButton() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button type="button" onClick={() => setOpen(true)} className="shrink-0 rounded-full border border-border px-3 py-1 text-[11px] text-muted transition hover:border-accent hover:text-text">
        How AI is used
      </button>

      {open ? (
        <div className="fixed inset-0 z-[60] flex items-center justify-center bg-black/60 p-4" onClick={() => setOpen(false)}>
          <div className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-border bg-surface p-6 shadow-2xl" onClick={(event) => event.stopPropagation()}>
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-semibold text-text">How Hurricane Week uses AI</p>
              <button type="button" onClick={() => setOpen(false)} aria-label="Close" className="rounded-full p-1 text-muted hover:text-text">
                <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                  <path d="M6 6l12 12M18 6 6 18" />
                </svg>
              </button>
            </div>
            <p className="mt-1 text-xs text-muted">You stay in control of your data and your outcome. No name, email, or account info is ever collected or sent to any AI provider.</p>

            <div className="mt-4 space-y-4">
              {capabilities.map((item) => (
                <div key={item.feature} className="rounded-2xl border border-border bg-background p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium text-text">{item.feature}</p>
                    <span className="rounded-full border border-accent/40 px-2 py-0.5 text-[10px] uppercase tracking-[0.1em] text-accent">{item.provider}</span>
                  </div>
                  <p className="mt-2 text-xs text-muted">
                    <span className="text-text">Shared: </span>
                    {item.shared}
                  </p>
                  <p className="mt-1 text-xs text-muted">
                    <span className="text-text">Purpose: </span>
                    {item.purpose}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-4 rounded-2xl border border-border bg-background p-3 text-xs text-muted">
              <p className="text-text">AI can: explain, personalize, and narrate.</p>
              <p className="mt-1 text-text">AI cannot: change your score, financial losses, storm conditions, or simulation outcomes.</p>
              <p className="mt-2">Every consequence in Hurricane Week comes from a deterministic rules engine, not an AI model. AI explains your outcome - it doesn&apos;t decide it.</p>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
