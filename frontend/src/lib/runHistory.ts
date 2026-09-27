import type { FinalReport, RunSummary } from "@/lib/types";

const STORAGE_KEY = "hurricane-week-previous-run";

function toSummary(report: FinalReport): RunSummary {
  return {
    outcome: report.outcome,
    overall_score: report.scores.overall,
    scores: {
      safety: report.scores.safety,
      financial: report.scores.financial,
      preparedness: report.scores.preparedness,
      timing: report.scores.timing,
    },
    decision_history: report.decision_history,
    financial_summary: report.financial_summary,
  };
}

export function loadPreviousRun(): RunSummary | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as RunSummary) : null;
  } catch {
    return null;
  }
}

export function saveRunAsPrevious(report: FinalReport): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(toSummary(report)));
  } catch {
    // ignore storage errors (private browsing, quota, etc.) - comparison is a bonus feature
  }
}
