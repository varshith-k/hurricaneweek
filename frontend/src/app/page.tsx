"use client";

import { useCallback, useEffect, useMemo, useReducer } from "react";

import { SetupScreen } from "@/components/SetupScreen";
import { Disclaimer, ErrorBanner, LandfallReveal, LoadingState, OutcomeBadge, PlacePanel, SafetyGateNotice, ScoreBars } from "@/components/common";
import { getActionText } from "@/content/actions";
import { disclaimer, safetyGateNotice, stageSituationCopy } from "@/content/copy";
import { getStageLabel } from "@/content/stages";
import { createSimulation, getCurrentEvent, getFinalReport, submitDecision } from "@/lib/client";
import { formatCurrency, formatSignedCurrency, humanize } from "@/lib/format";
import type { ApiError, PlayerProfile } from "@/lib/types";
import { initialState, simReducer } from "@/state/simReducer";

const stageOrder = ["T_MINUS_120", "T_MINUS_96", "T_MINUS_72", "T_MINUS_48", "T_MINUS_24", "LANDFALL", "RECOVERY"] as const;

// Keeps the loading screen (and its storm vortex animation) visible for at
// least this long, even if the API responds faster - otherwise fast
// same-datacenter round-trips make it flash by unnoticed.
const MIN_LOADING_MS = 700;

async function withMinDelay<T>(promise: Promise<T>): Promise<T> {
  const [result] = await Promise.all([promise, new Promise((resolve) => setTimeout(resolve, MIN_LOADING_MS))]);
  return result;
}

const saveSimulationId = (id: string | null) => {
  if (typeof window === "undefined") return;
  if (id) {
    sessionStorage.setItem("hurricane-week-sim", id);
  } else {
    sessionStorage.removeItem("hurricane-week-sim");
  }
};

export default function Home() {
  const [state, dispatch] = useReducer(simReducer, initialState);

  const useMockSession = state.useMock || process.env.NEXT_PUBLIC_USE_MOCK === "true";

  const handleToggleMock = useCallback((value: boolean) => {
    dispatch({ type: "SET_MOCK", value });
  }, []);

  const startNewGame = useCallback(
    async (profile: PlayerProfile) => {
      dispatch({ type: "START_LOAD", profile, useMock: useMockSession });
      try {
        const { created, event } = await withMinDelay(
          (async () => {
            const created = await createSimulation(profile);
            const event = await getCurrentEvent(created.simulation_id);
            return { created, event };
          })(),
        );
        saveSimulationId(created.simulation_id);
        dispatch({ type: "LOAD_EVENT", simulationId: created.simulation_id, event, state: created.state, useMock: useMockSession });
      } catch (error) {
        const apiError = error as ApiError;
        dispatch({ type: "SET_ERROR", message: apiError.message || "Could not start the simulation." });
      }
    },
    [useMockSession],
  );

  const retryCurrentGame = useCallback(async () => {
    if (!state.profile) return;
    await startNewGame(state.profile);
  }, [startNewGame, state.profile]);

  const restoreSession = useCallback(async () => {
    if (typeof window === "undefined") return;
    const storedId = sessionStorage.getItem("hurricane-week-sim");
    if (!storedId) return;
    try {
      const event = await getCurrentEvent(storedId);
      dispatch({
        type: "LOAD_EVENT",
        simulationId: storedId,
        event,
        state: {
          stage: event.stage,
          status: "active",
          simulation_complete: false,
          cash: 400,
          food_days: 1,
          water_days: 1,
          evacuated: false,
          scooter_protected: false,
          documents_secured: false,
          insurance_verified: false,
          transport_available: true,
          preparedness_points: 0,
          timing_points: 0,
          financial_loss: 0,
          completed_events: [],
          storm: { stage: event.stage, wind_mph: 0, flood_risk: 0 },
          scores: { safety: 0, financial: 0, preparedness: 0, timing: 0, overall: 0 },
        },
        useMock: useMockSession,
      });
    } catch (error) {
      const apiError = error as ApiError;
      if (apiError.status === 404) {
        dispatch({ type: "SESSION_RESTORE_FAILED" });
      } else {
        dispatch({ type: "SET_ERROR", message: apiError.message || "The session could not be restored." });
      }
    }
  }, [useMockSession]);

  useEffect(() => {
    void restoreSession();
  }, [restoreSession]);

  const currentStageIndex = useMemo(() => {
    if (!state.currentState?.stage) return 0;
    return stageOrder.indexOf(state.currentState.stage as (typeof stageOrder)[number]);
  }, [state.currentState]);

  const currentChoices = state.currentEvent?.choices ?? [];

  const submitChoice = useCallback(async () => {
    if (!state.currentEvent || !state.simulationId || !state.selectedChoiceId) return;
    dispatch({ type: "START_LOAD", profile: state.profile ?? { cash_on_hand: 400, has_insurance: false, housing_type: "apartment", transport_type: "scooter", household_size: 1, needs_refrigerated_medication: false }, useMock: useMockSession });
    try {
      const response = await withMinDelay(submitDecision(state.simulationId, state.currentEvent.event_id, state.selectedChoiceId));
      if (response.status === "completed") {
        const finalReport = response.final_report ?? (await getFinalReport(state.simulationId));
        dispatch({ type: "SET_CONSEQUENCE", outcome: response.outcome, state: response.state, nextEvent: null, finalReport });
        return;
      }
      dispatch({
        type: "SET_CONSEQUENCE",
        outcome: response.outcome,
        state: response.state,
        nextEvent: response.next_event,
        finalReport: response.final_report,
      });
    } catch (error) {
      const apiError = error as ApiError;
      dispatch({ type: "SET_ERROR", message: apiError.message || "The decision could not be submitted." });
    }
  }, [state.currentEvent, state.profile, state.selectedChoiceId, state.simulationId, useMockSession]);

  if (state.phase === "setup") {
    return (
      <main className="min-h-screen bg-background text-text">
        <SetupScreen onStart={startNewGame} onToggleMock={handleToggleMock} defaultMock={useMockSession} errorMessage={state.errorMessage} onClearError={() => dispatch({ type: "RESET" })} />
      </main>
    );
  }

  if (state.phase === "loading") {
    return (
      <main className="min-h-screen bg-background p-6 text-text">
        <div className="mx-auto max-w-4xl"><LoadingState /></div>
        <Disclaimer />
      </main>
    );
  }

  if (state.phase === "error") {
    return (
      <main className="min-h-screen bg-background p-6 text-text">
        <div className="mx-auto max-w-4xl">
          <ErrorBanner message={state.errorMessage ?? "Something went wrong."} onRetry={retryCurrentGame} onReset={() => { saveSimulationId(null); dispatch({ type: "RESET" }); }} />
        </div>
        <Disclaimer />
      </main>
    );
  }

  if (state.phase === "choosing" && state.currentEvent) {
    const progress = ((currentStageIndex + 1) / stageOrder.length) * 100;
    const hoursToLandfall = state.currentEvent.hours_to_landfall ?? Math.max(0, 120 - currentStageIndex * 24);
    const stageSituation = stageSituationCopy[state.currentEvent.stage] ?? "Your next decision changes what you carry into the next stage.";
    return (
      <main className="min-h-screen bg-background text-text">
        <div className="mx-auto max-w-7xl p-4 md:p-6">
          <div className="grid gap-5 xl:grid-cols-[1.1fr_1.5fr_0.95fr]">
            <aside className="rounded-3xl border border-border bg-surface p-5">
              <p className="text-xs uppercase tracking-[0.25em] text-muted">Vitals</p>
              <div className="mt-4 text-4xl font-semibold text-text">{formatCurrency(state.currentState?.cash ?? 0)}</div>
              <div className="mt-4 space-y-2 text-sm text-muted">
                <div className="flex items-center justify-between"><span>Food days</span><span className="font-medium text-text">{state.currentState?.food_days ?? 0}</span></div>
                <div className="flex items-center justify-between"><span>Water days</span><span className="font-medium text-text">{state.currentState?.water_days ?? 0}</span></div>
                <div className="flex items-center justify-between"><span>Scooter protected</span><span>{state.currentState?.scooter_protected ? "✓" : "—"}</span></div>
                <div className="flex items-center justify-between"><span>Documents secured</span><span>{state.currentState?.documents_secured ? "✓" : "—"}</span></div>
                <div className="flex items-center justify-between"><span>Insurance verified</span><span>{state.currentState?.insurance_verified ? "✓" : "—"}</span></div>
                <div className="flex items-center justify-between"><span>Evacuated</span><span>{state.currentState?.evacuated ? "✓" : "—"}</span></div>
                <div className="flex items-center justify-between"><span>Transport available</span><span>{state.currentState?.transport_available ? "✓" : "—"}</span></div>
              </div>
            </aside>

            <section className="rounded-3xl border border-border bg-surface p-5">
              <div className="mb-3 flex items-end justify-between gap-3">
                <div>
                  <span className="text-xs uppercase tracking-[0.25em] text-muted">{getStageLabel(state.currentEvent.stage)}</span>
                  <div className="mt-1 text-5xl font-semibold tracking-tight text-text">T−{String(hoursToLandfall).padStart(2, "0")}h</div>
                </div>
                <span className="text-sm text-muted">Step {Math.min(currentStageIndex + 1, stageOrder.length)} of 7</span>
              </div>
              <div className="mb-4 h-2 rounded-full bg-border">
                <div className="h-2 rounded-full bg-accent" style={{ width: `${progress}%` }} />
              </div>
              <p className="mb-4 text-sm italic text-muted">{stageSituation}</p>
              <h2 className="text-2xl font-semibold text-text">{state.currentEvent.title}</h2>
              <p className="mt-3 text-base text-muted">{state.currentEvent.description}</p>
              <div className="mt-5 space-y-3">
                {currentChoices.map((choice, index) => {
                  const isSelected = state.selectedChoiceId === choice.choice_id;
                  const canAfford = (state.currentState?.cash ?? 0) + (choice.cost ?? 0) >= 0;
                  return (
                    <button
                      key={choice.choice_id}
                      type="button"
                      onClick={() => dispatch({ type: "SELECT_CHOICE", choiceId: choice.choice_id })}
                      className={`w-full rounded-2xl border p-3 text-left transition ${isSelected ? "border-accent bg-accent/10" : "border-border bg-background hover:border-accent"} ${!canAfford ? "opacity-50" : ""}`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-[10px] uppercase tracking-[0.2em] text-muted">Choice {index + 1}</div>
                          <div className="mt-1 text-base font-medium text-text">{choice.label}</div>
                        </div>
                        {choice.cost !== undefined ? <span className="text-sm text-muted">{formatSignedCurrency(choice.cost)}</span> : null}
                      </div>
                      {!canAfford ? <div className="mt-2 text-xs text-danger">Not enough cash</div> : null}
                    </button>
                  );
                })}
              </div>
              <div className="mt-5 flex items-center gap-3">
                <button type="button" onClick={submitChoice} disabled={!state.selectedChoiceId} className="rounded-full bg-accent px-4 py-2.5 font-medium text-background disabled:cursor-not-allowed disabled:opacity-60">Lock in decision</button>
                <span className="text-sm text-muted">{state.selectedChoiceId ? "Choice selected" : "Select a choice"}</span>
              </div>
            </section>

            <div className="space-y-5">
              {state.currentState ? <PlacePanel state={state.currentState} /> : null}
              <aside className="rounded-3xl border border-border bg-surface p-5">
                <div className="flex items-center justify-between">
                  <p className="text-xs uppercase tracking-[0.25em] text-muted">Storm</p>
                  <span className="rounded-full border border-border px-2 py-1 text-[10px] uppercase tracking-[0.2em] text-muted">Simulated</span>
                </div>
                <div className="mt-4 rounded-2xl border border-border bg-background p-4">
                  <div className="flex items-center justify-between"><span className="text-sm text-muted">Wind</span><span className="font-medium text-text">{state.currentState?.storm.wind_mph ?? 0} mph</span></div>
                  <div className="mt-3 flex items-center justify-between"><span className="text-sm text-muted">Modeled flood risk</span><span className="font-medium text-text">{Math.round(((state.currentState?.storm.flood_risk ?? 0) * 100))}%</span></div>
                  {state.currentEvent.probability !== undefined ? <div className="mt-3 flex items-center justify-between"><span className="text-sm text-muted">Probability</span><span className="font-medium text-text">{Math.round(state.currentEvent.probability * 100)}%</span></div> : null}
                </div>
                <div className="mt-4 h-36 rounded-2xl border border-border bg-background p-3">
                  <div className="storm-graphic h-full w-full" aria-label="Simulated storm graphic" title="Simulated storm" />
                </div>
              </aside>
            </div>
          </div>
          <Disclaimer />
        </div>
      </main>
    );
  }

  if (state.phase === "consequence" && state.outcome) {
    return (
      <main className="min-h-screen bg-background p-6 text-text">
        <div className="mx-auto max-w-2xl rounded-3xl border border-border bg-surface p-6">
          {state.currentEvent?.stage === "LANDFALL" && state.currentState ? <LandfallReveal state={state.currentState} /> : null}
          <p className="text-xs uppercase tracking-[0.25em] text-accent">Story beat · Simulated</p>
          <div className="mt-4 rounded-2xl border border-border bg-background p-4" aria-live="polite">
            <p className="text-lg text-text">{state.outcome.consequence}</p>
            <p className="mt-3 text-base text-muted">Cash change: {formatSignedCurrency(state.outcome.cash_delta)}</p>
          </div>
          <button type="button" onClick={() => dispatch({ type: "CONTINUE_TO_NEXT" })} className="mt-5 rounded-full bg-accent px-5 py-3 font-medium text-background">Continue</button>
        </div>
        <Disclaimer />
      </main>
    );
  }

  if (state.phase === "report" && state.finalReport) {
    const report = state.finalReport;
    const showSafetyGate = report.scores.safety < 40;
    const actionText = report.action_identifiers.map((id) => getActionText(id));

    return (
      <main className="min-h-screen bg-background text-text print:bg-white">
        <div className="mx-auto max-w-6xl p-4 md:p-6">
          <div className="rounded-3xl border border-border bg-surface p-5 md:p-6">
            <div className="mb-6 flex flex-col gap-2 border-b border-border pb-5 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-accent">Post-storm debrief</p>
                <h1 className="mt-2 text-3xl font-semibold text-text md:text-4xl">Your Hurricane Week report</h1>
              </div>
              <span className="rounded-full border border-border px-3 py-1 text-xs uppercase tracking-[0.2em] text-muted">Simulated</span>
            </div>
            <OutcomeBadge outcome={report.outcome} />
            <SafetyGateNotice show={showSafetyGate} message={safetyGateNotice} />
            <div className="mt-6 grid gap-5 lg:grid-cols-[1.2fr_1.2fr_0.8fr]">
              <div className="rounded-2xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Overall score</p>
                <div className="mt-2 text-4xl font-semibold text-text">{report.scores.overall}</div>
                <div className="mt-5"><ScoreBars scores={report.scores} /></div>
              </div>
              <div className="rounded-2xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Score radar</p>
                <svg viewBox="0 0 220 220" className="mt-3 w-full">
                  <polygon points="110,20 170,70 170,150 110,200 50,150 50,70" fill="none" stroke="rgba(148,163,184,0.55)" />
                  <polygon points="110,80 170,110 150,170 90,180 55,130" fill="rgba(94,234,212,0.22)" stroke="#5eead4" strokeWidth="2" />
                </svg>
              </div>
              <div className="rounded-2xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Financial summary</p>
                <div className="mt-4 space-y-3 text-sm text-muted">
                  <div className="flex items-center justify-between"><span>Starting cash</span><span className="font-medium text-text">{formatCurrency(report.financial_summary.starting_cash)}</span></div>
                  <div className="flex items-center justify-between"><span>Ending cash</span><span className="font-medium text-text">{formatCurrency(report.financial_summary.ending_cash)}</span></div>
                  <div className="flex items-center justify-between"><span>Damage</span><span className="font-medium text-text">{formatCurrency(report.financial_summary.damage)}</span></div>
                </div>
              </div>
            </div>

            {report.insurance_breakdown ? <div className="mt-6 rounded-2xl border border-border bg-background p-4">...</div> : null}
            {report.decision_quality ? <div className="mt-6 rounded-2xl border border-border bg-background p-4">...</div> : null}

            <div className="mt-6 grid gap-5 md:grid-cols-2">
              <div className="rounded-2xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Strengths</p>
                <ul className="mt-3 space-y-2 text-sm text-text">{report.strengths.map((item) => <li key={item}>• {item}</li>)}</ul>
              </div>
              <div className="rounded-2xl border border-border bg-background p-4">
                <p className="text-xs uppercase tracking-[0.2em] text-muted">Preparedness gaps</p>
                <ul className="mt-3 space-y-2 text-sm text-text">{report.preparedness_gaps.map((item) => <li key={item}>• {item}</li>)}</ul>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-border bg-background p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted">What to do before the next storm</p>
              <ul className="mt-3 space-y-3 text-sm text-text">{actionText.map((item) => <li key={item}>• {item}</li>)}</ul>
            </div>

            {report.plan_text ? <div className="mt-6 rounded-2xl border border-border bg-background p-4"><p className="text-xs uppercase tracking-[0.2em] text-muted">Plan</p><p className="mt-3 text-sm text-text">{report.plan_text}</p></div> : null}
            {report.community_stat ? <div className="mt-6 rounded-2xl border border-border bg-background p-4"><p className="text-xs uppercase tracking-[0.2em] text-muted">Community stat</p><p className="mt-3 text-sm text-text">{report.community_stat.text}</p></div> : null}
            {report.audio_url ? <div className="mt-6 rounded-2xl border border-border bg-background p-4"><p className="text-xs uppercase tracking-[0.2em] text-muted">Spoken debrief</p><audio className="mt-3 w-full" controls src={report.audio_url}>Your browser does not support audio playback.</audio></div> : null}
            {report.solana_tx_url ? <div className="mt-6 rounded-2xl border border-border bg-background p-4"><p className="text-xs uppercase tracking-[0.2em] text-muted">On-chain record</p><p className="mt-2 text-sm text-muted">Your outcome and score were recorded as a verifiable transaction on Solana devnet.</p><a href={report.solana_tx_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 text-sm font-medium text-accent transition hover:border-accent">Verify on Solana Explorer<span aria-hidden="true">→</span></a></div> : null}

            <div className="mt-6 rounded-2xl border border-border bg-background p-4">
              <p className="text-xs uppercase tracking-[0.2em] text-muted">Decision timeline</p>
              <div className="mt-3 space-y-3">{report.decision_history.map((item) => <div key={`${item.stage}-${item.event_id}`} className="rounded-xl border border-border p-3"><div className="flex items-center justify-between gap-3"><span className="font-medium text-text">{getStageLabel(item.stage)}</span><span className="text-xs text-muted">{humanize(item.event_id)}</span></div><div className="mt-2 text-sm text-muted">Choice: {humanize(item.choice_id)}</div><div className="mt-1 text-sm text-text">{item.consequence}</div></div>)}</div>
            </div>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <button type="button" onClick={() => { saveSimulationId(null); window.location.reload(); }} className="rounded-full bg-accent px-5 py-3 font-medium text-background">Play again</button>
              <span className="text-sm text-muted">{disclaimer}</span>
            </div>
          </div>
          <Disclaimer />
        </div>
      </main>
    );
  }

  return <main className="min-h-screen bg-background p-6 text-text"><div className="mx-auto max-w-4xl"><LoadingState /></div><Disclaimer /></main>;
}
