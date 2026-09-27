import type { DecisionOutcome, EventResponse, FinalReport, PlayerProfile, SimulationState } from "@/lib/types";

export type Phase = "setup" | "loading" | "choosing" | "submitting" | "consequence" | "report" | "error";

export interface SimReducerState {
  phase: Phase;
  profile: PlayerProfile | null;
  simulationId: string | null;
  currentEvent: EventResponse | null;
  currentState: SimulationState | null;
  outcome: DecisionOutcome | null;
  finalReport: FinalReport | null;
  errorMessage: string | null;
  selectedChoiceId: string | null;
}

export const initialState: SimReducerState = {
  phase: "setup",
  profile: null,
  simulationId: null,
  currentEvent: null,
  currentState: null,
  outcome: null,
  finalReport: null,
  errorMessage: null,
  selectedChoiceId: null,
};

export type SimAction =
  | { type: "START_LOAD"; profile: PlayerProfile }
  | { type: "LOAD_EVENT"; simulationId: string; event: EventResponse; state: SimulationState }
  | { type: "SET_ERROR"; message: string }
  | { type: "SET_CONSEQUENCE"; outcome: DecisionOutcome; state: SimulationState; nextEvent: EventResponse | null; finalReport: FinalReport | null }
  | { type: "CONTINUE_TO_NEXT" }
  | { type: "SHOW_REPORT"; report: FinalReport }
  | { type: "RESET" }
  | { type: "SESSION_RESTORE_FAILED" }
  | { type: "SELECT_CHOICE"; choiceId: string };

export function simReducer(state: SimReducerState, action: SimAction): SimReducerState {
  switch (action.type) {
    case "START_LOAD":
      return {
        ...state,
        phase: "loading",
        profile: action.profile,
        errorMessage: null,
      };
    case "LOAD_EVENT":
      return {
        ...state,
        phase: "choosing",
        simulationId: action.simulationId,
        currentEvent: action.event,
        currentState: action.state,
        outcome: null,
        finalReport: null,
        selectedChoiceId: null,
        errorMessage: null,
      };
    case "SET_ERROR":
      return {
        ...state,
        phase: "error",
        errorMessage: action.message,
      };
    case "SET_CONSEQUENCE":
      return {
        ...state,
        phase: "consequence",
        outcome: action.outcome,
        currentState: action.state,
        currentEvent: action.nextEvent ?? state.currentEvent,
        finalReport: action.finalReport,
        selectedChoiceId: null,
        errorMessage: null,
      };
    case "CONTINUE_TO_NEXT":
      return {
        ...state,
        phase: state.finalReport ? "report" : "choosing",
        currentState: state.currentState,
        outcome: null,
      };
    case "SHOW_REPORT":
      return {
        ...state,
        phase: "report",
        finalReport: action.report,
        outcome: null,
      };
    case "RESET":
      return { ...initialState };
    case "SESSION_RESTORE_FAILED":
      return {
        ...state,
        phase: "setup",
        errorMessage: "This session expired (the server restarted). Start a new run.",
      };
    case "SELECT_CHOICE":
      return {
        ...state,
        selectedChoiceId: action.choiceId,
        errorMessage: null,
      };
    default:
      return state;
  }
}
