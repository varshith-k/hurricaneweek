import type { ReactNode } from "react";

import { disclaimer, generalCopy } from "@/content/copy";
import { formatCurrency, formatSignedCurrency } from "@/lib/format";
import type { FinalReport, ScoreState, SimulationState } from "@/lib/types";

export function Disclaimer() {
  return (
    <div className="mt-6 border-t border-border pt-4 text-sm text-muted">
      {disclaimer}
    </div>
  );
}

export function ErrorBanner({ message, onRetry, onReset }: { message: string; onRetry?: () => void; onReset?: () => void }) {
  return (
    <div className="rounded-2xl border border-danger/40 bg-danger/10 p-4 text-sm text-text">
      <p className="font-medium text-danger">Simulation error</p>
      <p className="mt-1 text-muted">{message}</p>
      <div className="mt-3 flex gap-2">
        {onRetry ? (
          <button type="button" onClick={onRetry} className="inline-flex rounded-full border border-border bg-surface px-3 py-2 text-sm font-medium text-text transition hover:border-accent">
            {generalCopy.retryLabel}
          </button>
        ) : null}
        {onReset ? (
          <button type="button" onClick={onReset} className="inline-flex rounded-full bg-accent px-3 py-2 text-sm font-medium text-background transition hover:opacity-90">
            {generalCopy.startOverLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}

export function LoadingState({ message = "Preparing your next decision..." }: { message?: string }) {
  return (
    <div className="space-y-4 rounded-2xl border border-border bg-surface p-4">
      <div className="h-4 w-1/3 animate-pulse rounded bg-border" />
      <div className="h-8 w-2/3 animate-pulse rounded bg-border" />
      <div className="h-16 animate-pulse rounded bg-border" />
      <p className="text-sm text-muted">{message}</p>
    </div>
  );
}

export function OutcomeBadge({ outcome }: { outcome: string }) {
  const tone = outcome.toLowerCase();
  const toneClass =
    tone.includes("highly resilient") || tone.includes("well prepared")
      ? "border-success/50 bg-success/10 text-success"
      : tone.includes("safe but exposed")
        ? "border-warning/50 bg-warning/10 text-warning"
        : tone.includes("high vulnerability") || tone.includes("critical vulnerability")
          ? "border-danger/50 bg-danger/10 text-danger"
          : "border-border bg-surface text-text";

  return <div className={`inline-flex rounded-full border px-3 py-1 text-sm font-semibold ${toneClass}`}>{outcome}</div>;
}

export function FinancialSummaryCard({ report }: { report: FinalReport }) {
  const { financial_summary } = report;
  return (
    <div className="rounded-2xl border border-border bg-surface p-4">
      <h3 className="text-sm uppercase tracking-[0.2em] text-muted">Financial summary</h3>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Starting cash</p>
          <p className="mt-1 text-xl font-semibold text-text">{formatCurrency(financial_summary.starting_cash)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Ending cash</p>
          <p className="mt-1 text-xl font-semibold text-text">{formatCurrency(financial_summary.ending_cash)}</p>
        </div>
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-muted">Damage</p>
          <p className="mt-1 text-xl font-semibold text-text">{formatCurrency(financial_summary.damage)}</p>
        </div>
      </div>
    </div>
  );
}

export function ScoreBars({ scores }: { scores: ScoreState }) {
  const metrics = [
    { key: "safety", label: "Safety" },
    { key: "financial", label: "Financial resilience" },
    { key: "preparedness", label: "Preparedness" },
    { key: "timing", label: "Decision timing" },
  ] as const;

  return (
    <div className="space-y-4 rounded-2xl border border-border bg-surface p-4">
      {metrics.map((metric) => (
        <div key={metric.key}>
          <div className="mb-1 flex items-center justify-between text-sm text-muted">
            <span>{metric.label}</span>
            <span className="font-medium text-text">{scores[metric.key]}</span>
          </div>
          <div className="h-2 rounded-full bg-border">
            <div className="h-2 rounded-full bg-accent" style={{ width: `${scores[metric.key]}%` }} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SafetyGateNotice({ show, message }: { show: boolean; message: string }) {
  if (!show) return null;
  return (
    <div className="rounded-2xl border border-danger/40 bg-danger/10 p-4 text-danger">
      <p className="font-semibold">Safety check</p>
      <p className="mt-1 text-sm">{message}</p>
    </div>
  );
}

export function CardTitle({ children }: { children: ReactNode }) {
  return <h3 className="text-sm uppercase tracking-[0.18em] text-muted">{children}</h3>;
}

export function currencyDeltaText(value: number) {
  return formatSignedCurrency(value);
}

function InlineIcon({ children, label }: { children: ReactNode; label: string }) {
  return (
    <svg viewBox="0 0 48 48" role="img" aria-label={label} className="h-10 w-10 shrink-0 text-accent" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      {children}
    </svg>
  );
}

function ApartmentIcon({ evacuated }: { evacuated: boolean }) {
  return (
    <InlineIcon label={evacuated ? "Apartment left safely" : "Apartment exposed in place"}>
      <path d="M8 42h32M12 42V13l12-7 12 7v29M18 42V28h12v14M18 18h4M26 18h4M18 23h4M26 23h4" />
      {evacuated ? <path d="m35 9 3 3 6-7" className="text-success" /> : <path d="M35 8h8M39 4v8" className="text-warning" />}
    </InlineIcon>
  );
}

function ScooterIcon({ protectedScooter }: { protectedScooter: boolean }) {
  return (
    <InlineIcon label={protectedScooter ? "Scooter protected indoors" : "Scooter exposed outdoors"}>
      <circle cx="14" cy="35" r="6" />
      <circle cx="35" cy="35" r="6" />
      <path d="M14 35h10l5-13h7l3 13M24 35l-5-12h7l3 6M32 22l2-5h5" />
      {protectedScooter ? <path d="M8 10h32M8 10v28M40 10v28" className="text-success" /> : null}
    </InlineIcon>
  );
}

function LaptopIcon({ secured }: { secured: boolean }) {
  return (
    <InlineIcon label={secured ? "Laptop and work items secured" : "Laptop and work items unsecured"}>
      <rect x="10" y="10" width="28" height="21" rx="2" />
      <path d="M6 37h36l-4 4H10l-4-4ZM21 26h6" />
      {secured ? <path d="m32 16 2 2 4-5" className="text-success" /> : null}
    </InlineIcon>
  );
}

function SuppliesIcon({ waterDays, foodDays }: { waterDays: number; foodDays: number }) {
  const bottleCount = Math.min(3, Math.max(0, waterDays));
  return (
    <InlineIcon label={`${waterDays} days of water and ${foodDays} days of food`}>
      <path d="M10 18h12v22H10zM13 12h6v6h-6zM28 24h10v16H28zM30 19h6v5h-6z" />
      {Array.from({ length: bottleCount }, (_, index) => <path key={index} d={`M${14 + index * 6} 14v-4`} className="text-success" />)}
      <path d="M31 30h4M31 34h4" className={foodDays >= 3 ? "text-success" : "text-warning"} />
    </InlineIcon>
  );
}

function DocumentsIcon({ secured }: { secured: boolean }) {
  return (
    <InlineIcon label={secured ? "Documents secured" : "Documents unsecured"}>
      <path d="M13 7h16l7 7v27H13zM29 7v8h7M18 24h13M18 30h13M18 36h8" />
      {secured ? <path d="m32 35 3 3 6-7" className="text-success" /> : null}
    </InlineIcon>
  );
}

export function PlacePanel({ state }: { state: SimulationState }) {
  const items = [
    { label: "Apartment", detail: state.evacuated ? "Left before peak risk" : "You are staying put", icon: <ApartmentIcon evacuated={state.evacuated} /> },
    { label: "Scooter", detail: state.scooter_protected ? "Moved indoors" : "Still exposed", icon: <ScooterIcon protectedScooter={state.scooter_protected} /> },
    { label: "Laptop", detail: state.documents_secured ? "Work items secured" : "Still at home", icon: <LaptopIcon secured={state.documents_secured} /> },
    { label: "Supplies", detail: `${state.water_days} water days · ${state.food_days} food days`, icon: <SuppliesIcon waterDays={state.water_days} foodDays={state.food_days} /> },
    { label: "Documents", detail: state.documents_secured ? "Secured" : "Not secured", icon: <DocumentsIcon secured={state.documents_secured} /> },
  ];

  return (
    <aside className="rounded-3xl border border-border bg-surface p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs uppercase tracking-[0.25em] text-muted">Your place</p>
        <span className="rounded-full border border-border px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-muted">Simulated</span>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-1">
        {items.map((item) => (
          <div key={item.label} className="flex items-center gap-3 rounded-2xl border border-border bg-background p-3">
            {item.icon}
            <div className="min-w-0">
              <p className="text-sm font-medium text-text">{item.label}</p>
              <p className="mt-1 text-xs text-muted">{item.detail}</p>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}

type RevealItem = { label: string; safe: boolean; reason: string };

export function LandfallReveal({ state }: { state: SimulationState }) {
  const items: RevealItem[] = [
    { label: "Place", safe: state.evacuated, reason: state.evacuated ? "You moved before peak risk." : "You stayed in place through peak risk." },
    { label: "Scooter", safe: state.scooter_protected, reason: state.scooter_protected ? "It was moved to protected storage." : "It remained exposed during the storm." },
    { label: "Supplies", safe: state.water_days >= 3 && state.food_days >= 3, reason: state.water_days >= 3 && state.food_days >= 3 ? "Your stored supplies cover the modeled need." : "Your stored supplies are below the modeled need." },
    { label: "Documents", safe: state.documents_secured, reason: state.documents_secured ? "Critical documents were secured." : "Critical documents were not secured before landfall." },
  ];

  return (
    <div className="landfall-reveal -mx-6 -mt-6 mb-6 rounded-t-3xl p-6" aria-live="polite">
      <div className="rain-overlay" aria-hidden="true" />
      <div className="relative">
        <p className="text-xs uppercase tracking-[0.25em] text-accent">Landfall reveal · Simulated</p>
        <h2 className="mt-2 text-3xl font-semibold text-text">What held through the storm?</h2>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {items.map((item, index) => (
            <div key={item.label} className="reveal-item rounded-2xl border border-border bg-surface/90 p-4" style={{ animationDelay: `${index * 180}ms` }}>
              <div className="flex items-center justify-between gap-3">
                <span className="font-medium text-text">{item.label}</span>
                <span className={item.safe ? "text-success" : "text-danger"}>{item.safe ? "Safe" : "Damaged"}</span>
              </div>
              <p className="mt-2 text-sm text-muted">{item.reason}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
