export type HousingType = "apartment" | "house" | "mobile_home";
export type TransportType = "car" | "scooter" | "public_transit";
export type SimulationStatus = "active" | "completed";
export type DecisionStatus = "in_progress" | "completed";

export interface PlayerProfile {
  cash_on_hand: number;
  has_insurance: boolean;
  housing_type: HousingType;
  transport_type: TransportType;
  household_size: number;
  needs_refrigerated_medication: boolean;
}

export interface StormState {
  stage: string;
  wind_mph: number;
  flood_risk: number;
}

export interface ScoreState {
  safety: number;
  financial: number;
  preparedness: number;
  timing: number;
  overall: number;
}

export interface SimulationState {
  stage: string;
  status: SimulationStatus;
  simulation_complete: boolean;
  cash: number;
  food_days: number;
  water_days: number;
  evacuated: boolean;
  scooter_protected: boolean;
  documents_secured: boolean;
  insurance_verified: boolean;
  transport_available: boolean;
  preparedness_points: number;
  timing_points: number;
  financial_loss: number;
  completed_events: string[];
  storm: StormState;
  scores: ScoreState;
}

export interface EventChoice {
  choice_id: string;
  label: string;
  cost?: number;
  hours?: number;
}

export interface EventResponse {
  simulation_id: string;
  event_id: string;
  stage: string;
  title: string;
  description: string;
  choices: EventChoice[];
  simulation_complete: boolean;
  probability?: number;
  stage_label?: string;
  hours_to_landfall?: number;
}

export interface DecisionOutcome {
  consequence: string;
  cash_delta: number;
  preparedness_delta: number;
  timing_delta: number;
}

export interface DecisionResponse {
  simulation_id: string;
  status: DecisionStatus;
  outcome: DecisionOutcome;
  state: SimulationState;
  next_event: EventResponse | null;
  final_report: FinalReport | null;
}

export interface FinancialSummary {
  starting_cash: number;
  ending_cash: number;
  damage: number;
}

export interface InsuranceBreakdownItem {
  item: string;
  cause: string;
  covered: boolean;
  deductible: number;
  payout: number;
  reason: string;
}

export interface DecisionQualityOption {
  label: string;
  expected_loss: number;
  chosen: boolean;
}

export interface DecisionQualityEntry {
  stage: string;
  probability: number;
  options: DecisionQualityOption[];
}

export interface CommunityStat {
  text: string;
  count: number;
}

export interface RentSummary {
  owed: number;
  paid: boolean;
  late_fee: number;
}

export interface FinalReport {
  simulation_id: string;
  outcome: string;
  scores: ScoreState;
  financial_summary: FinancialSummary;
  strengths: string[];
  preparedness_gaps: string[];
  action_identifiers: string[];
  decision_history: Array<{
    stage: string;
    event_id: string;
    choice_id: string;
    consequence: string;
  }>;
  insurance_breakdown?: InsuranceBreakdownItem[];
  decision_quality?: DecisionQualityEntry[];
  plan_text?: string;
  community_stat?: CommunityStat;
  audio_url?: string;
  rent?: RentSummary;
}

export interface ApiError extends Error {
  status: number;
  message: string;
}

export interface SimulationCreateResponse {
  simulation_id: string;
  state: SimulationState;
}
