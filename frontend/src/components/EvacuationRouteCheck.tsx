"use client";

import { useState } from "react";

import { getEvacuationRoute } from "@/lib/api";
import type { EvacuationRoute } from "@/lib/types";

const MODE_LABEL: Record<string, string> = {
  "driving-car": "Car",
  "cycling-regular": "Scooter (bike-equivalent route)",
  "foot-walking": "On foot (no personal vehicle)",
};

export function EvacuationRouteCheck({ simulationId }: { simulationId: string }) {
  const [route, setRoute] = useState<EvacuationRoute | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const check = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await getEvacuationRoute(simulationId);
      setRoute(result);
    } catch {
      setError("Could not check the route right now.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-4 rounded-2xl border border-border bg-background p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs uppercase tracking-[0.2em] text-muted">Evacuation mobility check</p>
        <button type="button" onClick={() => void check()} disabled={loading} className="rounded-full border border-border px-3 py-1.5 text-xs text-text transition hover:border-accent disabled:opacity-50">
          {loading ? "Checking..." : route ? "Recheck route" : "Check evacuation route"}
        </button>
      </div>

      {error ? <p className="mt-2 text-xs text-danger">{error}</p> : null}

      {route && !route.available ? <p className="mt-2 text-xs text-muted">{route.note}</p> : null}

      {route && route.available ? (
        <div className="mt-3 space-y-1.5 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-muted">Nearest shelter</span>
            <span className="text-text">
              {route.shelter_name} ({route.shelter_area})
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted">Transport</span>
            <span className="text-text">{route.transport_mode ? MODE_LABEL[route.transport_mode] ?? route.transport_mode : "—"}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted">Distance</span>
            <span className="text-text">{route.distance_km} km</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted">Est. travel time</span>
            <span className="text-text">{route.duration_min} min</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-muted">Route status</span>
            <span className={route.feasibility === "compromised" ? "text-warning" : "text-success"}>
              {route.feasibility === "compromised" ? "At risk" : "Clear"}
            </span>
          </div>
          {route.warning ? <p className="mt-2 rounded-xl border border-warning/30 bg-warning/10 p-2 text-xs text-warning">{route.warning}</p> : null}
          <p className="mt-2 text-[11px] text-muted/80">
            From {route.origin_label}. {route.note}
          </p>
        </div>
      ) : null}
    </div>
  );
}
