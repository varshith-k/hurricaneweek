"use client";

import { useEffect, useState } from "react";

import { getCoverageCheck } from "@/lib/api";
import type { CoverageResponse } from "@/lib/types";

export function CoverageCheck() {
  const [data, setData] = useState<CoverageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");

  useEffect(() => {
    getCoverageCheck()
      .then(setData)
      .catch(() => setError("Could not load coverage info right now."));
  }, []);

  if (error) {
    return <div className="rounded-xl border border-danger/30 bg-danger/10 p-3 text-xs text-danger">{error}</div>;
  }

  if (!data) {
    return <div className="p-4 text-xs text-muted">Loading...</div>;
  }

  const selected = data.entries.find((entry) => entry.id === selectedId);

  return (
    <div className="flex flex-1 flex-col overflow-y-auto p-4">
      <p className="text-sm text-text">What type of insurance policy do you have?</p>
      <p className="mt-1 text-[11px] text-muted">{data.disclaimer}</p>

      <select
        value={selectedId}
        onChange={(event) => setSelectedId(event.target.value)}
        className="mt-3 rounded-xl border border-border bg-background px-3 py-2 text-sm text-text outline-none focus:border-accent"
      >
        <option value="" disabled>
          Select a policy type...
        </option>
        {data.entries.map((entry) => (
          <option key={entry.id} value={entry.id}>
            {entry.label}
          </option>
        ))}
      </select>

      {selected ? (
        <div className="mt-4 space-y-3 rounded-2xl border border-border bg-background p-3 text-sm">
          <div>
            <p className="text-xs uppercase tracking-[0.15em] text-muted">Wind damage</p>
            <p className="mt-1 text-text">{selected.wind}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.15em] text-muted">Flood / storm surge</p>
            <p className="mt-1 text-text">{selected.flood}</p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.15em] text-muted">What to do</p>
            <p className="mt-1 text-text">{selected.action}</p>
          </div>
          <p className="text-[11px] text-muted/80">Source: {selected.source}</p>
        </div>
      ) : null}
    </div>
  );
}
