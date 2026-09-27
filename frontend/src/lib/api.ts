import type { ApiError, AskResponse, AssistantIntro, ChatTurn, CompareRunsResponse, CoverageResponse, DecisionResponse, EvacuationRoute, EventResponse, FinalReport, PlayerProfile, QuizResponse, RunSummary, SimulationCreateResponse } from "@/lib/types";

const DEFAULT_BASE = "http://localhost:8000/api";

export function buildApiBase(): string {
  return (process.env.NEXT_PUBLIC_API_BASE || DEFAULT_BASE).replace(/\/$/, "");
}

function normalizeError(status: number, message: string): ApiError {
  const error = new Error(message) as ApiError;
  error.status = status;
  error.message = message;
  return error;
}

async function request<T>(path: string, method: "GET" | "POST", body?: unknown): Promise<T> {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 10000);

  try {
    const response = await fetch(`${buildApiBase()}${path}`, {
      method,
      headers: {
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    if (!response.ok) {
      let message = "Request failed";
      try {
        const payload = (await response.json()) as { detail?: string };
        message = payload.detail ?? message;
      } catch {
        message = response.statusText || message;
      }
      throw normalizeError(response.status, message);
    }

    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw normalizeError(504, "Request timed out");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
}

export async function healthCheck(): Promise<{ status: string }> {
  return request<{ status: string }>("/health", "GET");
}

export async function createSimulation(profile: PlayerProfile): Promise<SimulationCreateResponse> {
  return request<SimulationCreateResponse>("/simulations", "POST", { player_profile: profile });
}

export async function getCurrentEvent(simulationId: string): Promise<EventResponse> {
  return request<EventResponse>(`/simulations/${simulationId}/event`, "GET");
}

export async function submitDecision(simulationId: string, eventId: string, choiceId: string): Promise<DecisionResponse> {
  return request<DecisionResponse>(`/simulations/${simulationId}/decisions`, "POST", {
    event_id: eventId,
    choice_id: choiceId,
  });
}

export async function getFinalReport(simulationId: string): Promise<FinalReport> {
  return request<FinalReport>(`/simulations/${simulationId}/report`, "GET");
}

export async function getAssistantIntro(simulationId?: string | null): Promise<AssistantIntro> {
  const query = simulationId ? `?simulation_id=${simulationId}` : "";
  return request<AssistantIntro>(`/assistant/intro${query}`, "GET");
}

export async function askAssistant(
  input: { question?: string; question_id?: string },
  simulationId?: string | null,
  history: ChatTurn[] = [],
): Promise<AskResponse> {
  return request<AskResponse>("/assistant/ask", "POST", {
    ...input,
    simulation_id: simulationId ?? undefined,
    history,
  });
}

export async function getAutoInsuranceQuiz(): Promise<QuizResponse> {
  return request<QuizResponse>("/quiz/auto-insurance", "GET");
}

export async function getEvacuationRoute(simulationId: string): Promise<EvacuationRoute> {
  return request<EvacuationRoute>(`/simulations/${simulationId}/evacuation-route`, "GET");
}

export async function compareRuns(previous: RunSummary, current: RunSummary): Promise<CompareRunsResponse> {
  return request<CompareRunsResponse>("/coach/compare-runs", "POST", { previous, current });
}

export async function getCoverageCheck(): Promise<CoverageResponse> {
  return request<CoverageResponse>("/coverage-check", "GET");
}
