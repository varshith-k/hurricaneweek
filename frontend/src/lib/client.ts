import * as api from "@/lib/api";
import * as mockApi from "@/lib/mockApi";
import type { DecisionResponse, EventResponse, FinalReport, PlayerProfile, SimulationCreateResponse } from "@/lib/types";

export const isMockMode = () => process.env.NEXT_PUBLIC_USE_MOCK === "true";

export async function healthCheck(): Promise<{ status: string }> {
  return isMockMode() ? mockApi.mockHealthCheck() : api.healthCheck();
}

export async function createSimulation(profile: PlayerProfile): Promise<SimulationCreateResponse> {
  return isMockMode() ? mockApi.mockCreateSimulation(profile) : api.createSimulation(profile);
}

export async function getCurrentEvent(simulationId: string): Promise<EventResponse> {
  return isMockMode() ? mockApi.mockGetCurrentEvent(simulationId) : api.getCurrentEvent(simulationId);
}

export async function submitDecision(simulationId: string, eventId: string, choiceId: string): Promise<DecisionResponse> {
  return isMockMode() ? mockApi.mockSubmitDecision(simulationId, eventId, choiceId) : api.submitDecision(simulationId, eventId, choiceId);
}

export async function getFinalReport(simulationId: string): Promise<FinalReport> {
  return isMockMode() ? mockApi.mockGetFinalReport(simulationId) : api.getFinalReport(simulationId);
}
