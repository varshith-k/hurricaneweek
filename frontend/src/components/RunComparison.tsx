"use client";

import { useEffect, useRef, useState } from "react";

import { compareRuns } from "@/lib/api";
import { formatCurrency } from "@/lib/format";
import { loadPreviousRun, saveRunAsPrevious } from "@/lib/runHistory";
import type { FinalReport, RunSummary } from "@/lib/types";

function DeltaRow({ label, previous, current, higherIsBetter, formatter }: { label: string; previous: number; current: number; higherIsBetter: boolean; formatter?: (value: number) => string }) {
  const diff = current - previous;
  const improved = higherIsBetter ? diff > 0 : diff < 0;
  const worsened = higherIsBetter ? diff < 0 : diff > 0;
  const format = formatter ?? ((value: number) => `${value}`);

  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-muted">{label}</span>
      <span className="flex items-center gap-2">
        <span className="text-muted">{format(previous)}</span>
        <span className="text-muted">→</span>
        <span className="font-medium text-text">{format(current)}</span>
        {diff !== 0 ? (
          <span className={improved ? "text-success" : worsened ? "text-danger" : "text-muted"}>
            {diff > 0 ? "↑" : "↓"}
            {format(Math.abs(diff))}
          </span>
        ) : null}
      </span>
    </div>
  );
}

export function RunComparison({ report }: { report: FinalReport }) {
  const [previous, setPrevious] = useState<RunSummary | null>(null);
  const [explanation, setExplanation] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const hasCapturedRef = useRef(false);

  useEffect(() => {
    // Guards against React Strict Mode's dev-only double-invoke: without this,
    // the second invocation reads back the first invocation's just-saved
    // write and shows a run compared against itself.
    if (hasCapturedRef.current) return;
    hasCapturedRef.current = true;
    setPrevious(loadPreviousRun());
    saveRunAsPrevious(report);
    // Runs once when the report first mounts - deliberately ignores `report` in deps
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!previous) return null;

  const current: RunSummary = {
    outcome: report.outcome,
    overall_score: report.scores.overall,
    scores: report.scores,
    decision_history: report.decision_history,
    financial_summary: report.financial_summary,
  };

  const whatChanged = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await compareRuns(previous, current);
      setExplanation(result.explanation ?? "No explanation was available for this comparison.");
    } catch {
      setError("Could not compare runs right now.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6 rounded-2xl border border-accent/40 bg-accent/5 p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.2em] text-accent">Try again - your progress</p>
        <button type="button" onClick={() => void whatChanged()} disabled={loading} className="shrink-0 rounded-full border border-accent/40 px-3 py-1 text-xs text-text transition hover:border-accent disabled:opacity-50">
          {loading ? "Thinking..." : "✨ What changed?"}
        </button>
      </div>

      <div className="mt-3 space-y-1.5">
        <DeltaRow label="Overall" previous={previous.overall_score} current={current.overall_score} higherIsBetter />
        <DeltaRow label="Safety" previous={previous.scores.safety} current={current.scores.safety} higherIsBetter />
        <DeltaRow label="Financial" previous={previous.scores.financial} current={current.scores.financial} higherIsBetter />
        <DeltaRow label="Preparedness" previous={previous.scores.preparedness} current={current.scores.preparedness} higherIsBetter />
        <DeltaRow label="Timing" previous={previous.scores.timing} current={current.scores.timing} higherIsBetter />
        <DeltaRow
          label="Damage"
          previous={previous.financial_summary.damage}
          current={current.financial_summary.damage}
          higherIsBetter={false}
          formatter={formatCurrency}
        />
      </div>

      {error ? <p className="mt-2 text-xs text-danger">{error}</p> : null}
      {explanation ? <p className="mt-3 rounded-xl border border-border bg-background p-3 text-sm text-text">{explanation}</p> : null}
    </div>
  );
}
