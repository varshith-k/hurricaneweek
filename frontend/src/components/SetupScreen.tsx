"use client";

import { useEffect, useState } from "react";

import { stageIntroCopy } from "@/content/copy";
import { Disclaimer } from "@/components/common";
import { healthCheck } from "@/lib/client";
import type { PlayerProfile } from "@/lib/types";

const defaultProfile: PlayerProfile = {
  cash_on_hand: 400,
  has_insurance: false,
  housing_type: "apartment",
  transport_type: "scooter",
  household_size: 1,
  needs_refrigerated_medication: false,
};

export function SetupScreen({
  onStart,
  onToggleMock,
  defaultMock,
  errorMessage,
  onClearError,
}: {
  onStart: (profile: PlayerProfile) => void;
  onToggleMock: (enabled: boolean) => void;
  defaultMock: boolean;
  errorMessage?: string | null;
  onClearError?: () => void;
}) {
  const [customizeOpen, setCustomizeOpen] = useState(false);
  const [profile, setProfile] = useState<PlayerProfile>(defaultProfile);
  const [backendOnline, setBackendOnline] = useState(true);
  const [mockEnabled, setMockEnabled] = useState(defaultMock);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        await healthCheck();
        if (!cancelled) setBackendOnline(true);
      } catch {
        if (!cancelled) setBackendOnline(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (errorMessage && onClearError) {
      const timer = window.setTimeout(() => onClearError(), 3500);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, [errorMessage, onClearError]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("demo") === "1") {
      onStart(defaultProfile);
    }
  }, [onStart]);

  const updateField = <K extends keyof PlayerProfile>(field: K, value: PlayerProfile[K]) => {
    setProfile((current) => ({ ...current, [field]: value }));
  };

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-6 py-8">
      <div className="rounded-3xl border border-border bg-surface p-6 shadow-lg shadow-black/10 md:p-8">
        <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-muted">Storm readiness</p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-text md:text-5xl">{stageIntroCopy.setupTitle}</h1>
            <p className="mt-3 max-w-xl text-lg text-muted">{stageIntroCopy.setupTagline}</p>
          </div>
          <div className="rounded-2xl border border-border bg-background p-3 text-sm text-muted">
            <div className="flex items-center gap-2">
              <span className={`inline-block h-2.5 w-2.5 rounded-full ${backendOnline ? "bg-success" : "bg-border"}`} />
              <span>{backendOnline ? "Engine online" : "Offline — demo mode available"}</span>
            </div>
            <label className="mt-3 flex items-center gap-2">
              <input
                type="checkbox"
                checked={mockEnabled}
                onChange={(event) => {
                  const enabled = event.target.checked;
                  setMockEnabled(enabled);
                  onToggleMock(enabled);
                }}
              />
              <span>Use mock mode</span>
            </label>
          </div>
        </div>
        <p className="mt-6 max-w-3xl text-base text-muted">
          Hurricane Week simulates the days before a storm so you can practice decisions with limited cash and a changing forecast. The choices here do not change the weather; they change how much risk you carry.
        </p>

        <div className="mt-8 flex flex-wrap items-center gap-3">
          <button type="button" onClick={() => onStart(profile)} className="rounded-full bg-accent px-5 py-3 font-medium text-background transition hover:opacity-90">
            Start the $400 Challenge
          </button>
          <button type="button" onClick={() => setCustomizeOpen((value) => !value)} className="rounded-full border border-border bg-background px-5 py-3 font-medium text-text transition hover:border-accent">
            Customize
          </button>
        </div>

        {errorMessage ? (
          <div className="mt-5 rounded-2xl border border-danger/30 bg-danger/10 p-3 text-sm text-danger">{errorMessage}</div>
        ) : null}

        {customizeOpen ? (
          <div className="mt-8 grid gap-4 rounded-2xl border border-border bg-background p-4 md:grid-cols-2">
            <label className="flex flex-col gap-1 text-sm text-muted">
              Cash on hand
              <input type="number" min={0} max={100000} value={profile.cash_on_hand} onChange={(event) => updateField("cash_on_hand", Number(event.target.value))} className="rounded-xl border border-border bg-surface px-3 py-2 text-text" />
            </label>
            <label className="flex flex-col gap-1 text-sm text-muted">
              Household size
              <input type="number" min={1} max={10} value={profile.household_size} onChange={(event) => updateField("household_size", Number(event.target.value))} className="rounded-xl border border-border bg-surface px-3 py-2 text-text" />
            </label>
            <label className="flex flex-col gap-1 text-sm text-muted">
              Housing type
              <select value={profile.housing_type} onChange={(event) => updateField("housing_type", event.target.value as PlayerProfile["housing_type"])} className="rounded-xl border border-border bg-surface px-3 py-2 text-text">
                <option value="apartment">Apartment</option>
                <option value="house">House</option>
                <option value="mobile_home">Mobile home</option>
              </select>
            </label>
            <label className="flex flex-col gap-1 text-sm text-muted">
              Transport type
              <select value={profile.transport_type} onChange={(event) => updateField("transport_type", event.target.value as PlayerProfile["transport_type"])} className="rounded-xl border border-border bg-surface px-3 py-2 text-text">
                <option value="car">Car</option>
                <option value="scooter">Scooter</option>
                <option value="public_transit">Public transit</option>
              </select>
            </label>
            <label className="flex items-center gap-2 text-sm text-muted">
              <input type="checkbox" checked={profile.has_insurance} onChange={(event) => updateField("has_insurance", event.target.checked)} />
              Has insurance
            </label>
            <label className="flex items-center gap-2 text-sm text-muted">
              <input type="checkbox" checked={profile.needs_refrigerated_medication} onChange={(event) => updateField("needs_refrigerated_medication", event.target.checked)} />
              Needs refrigerated medication
            </label>
          </div>
        ) : null}
      </div>
      <Disclaimer />
    </div>
  );
}
