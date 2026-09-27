"use client";

import { useEffect, useState } from "react";

import { stageIntroCopy } from "@/content/copy";
import { Disclaimer } from "@/components/common";
import { LandingSections } from "@/components/LandingSections";
import { healthCheck } from "@/lib/client";
import type { PlayerProfile } from "@/lib/types";

const navLinks = [
  { href: "#challenge", label: "The Challenge" },
  { href: "#how-it-works", label: "How It Works" },
  { href: "#features", label: "Features" },
];

const heroBadges = [
  { label: "Built for Disaster Prep", icon: "M12 2 4 5v6c0 5.25 3.5 9.74 8 11 4.5-1.26 8-5.75 8-11V5l-8-3z" },
  { label: "Interactive Simulation", icon: "M9 18h6M10 22h4M12 2a7 7 0 0 0-4 12.7V17h8v-2.3A7 7 0 0 0 12 2z" },
  { label: "Real-World Scenarios", icon: "M12 22s7-4.5 7-11a7 7 0 1 0-14 0c0 6.5 7 11 7 11z M12 8v4l2 2" },
];

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
    <div className="relative min-h-screen w-full overflow-hidden">
      <div className="absolute inset-0 h-[820px]">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/images/hero-storm-satellite.jpg" alt="" className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-b from-background/50 via-background/75 to-background" />
      </div>

      <div className="relative mx-auto w-full max-w-6xl px-4 pt-4">
        <nav className="flex items-center justify-between rounded-2xl border border-border bg-surface/70 px-4 py-3 shadow-lg shadow-black/20 backdrop-blur-md">
          <div className="flex items-center gap-2 text-text">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/icon.svg" alt="" className="h-6 w-6" />
            <span className="font-semibold">Hurricane Week</span>
          </div>
          <div className="hidden items-center gap-6 text-sm text-muted md:flex">
            {navLinks.map((link) => (
              <a key={link.href} href={link.href} className="transition hover:text-text">
                {link.label}
              </a>
            ))}
          </div>
          <button type="button" onClick={() => onStart(profile)} className="rounded-full bg-accent px-4 py-2 text-sm font-medium text-background transition hover:opacity-90">
            Play Now →
          </button>
        </nav>
      </div>

      <div className="relative mx-auto flex w-full max-w-6xl flex-col gap-6 px-4 pb-8 pt-2 md:pb-16">
        <div className="rounded-3xl border border-border bg-surface/70 p-6 shadow-lg shadow-black/30 backdrop-blur-md md:p-8">
          <div className="flex flex-col gap-6 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-muted">Storm readiness</p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight text-text md:text-5xl">{stageIntroCopy.setupTitle}</h1>
              <p className="mt-3 max-w-xl text-lg text-muted">{stageIntroCopy.setupTagline}</p>
              <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted">
                {heroBadges.map((badge) => (
                  <span key={badge.label} className="flex items-center gap-1.5">
                    <svg viewBox="0 0 24 24" className="h-3.5 w-3.5 text-accent" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d={badge.icon} />
                    </svg>
                    {badge.label}
                  </span>
                ))}
              </div>
            </div>
            <div className="rounded-2xl border border-border bg-background/80 p-3 text-sm text-muted backdrop-blur-sm">
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
            <button type="button" onClick={() => onStart(profile)} className="inline-flex items-center gap-2 rounded-full bg-accent px-5 py-3 font-medium text-background transition hover:opacity-90">
              Start the $400 Challenge
              <span aria-hidden="true">→</span>
            </button>
            <button type="button" onClick={() => setCustomizeOpen((value) => !value)} className="rounded-full border border-border bg-background/80 px-5 py-3 font-medium text-text backdrop-blur-sm transition hover:border-accent">
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
      </div>

      <div className="relative">
        <LandingSections onStart={() => onStart(profile)} />
        <div className="mx-auto max-w-6xl px-4 pb-10">
          <Disclaimer />
        </div>
      </div>
    </div>
  );
}
