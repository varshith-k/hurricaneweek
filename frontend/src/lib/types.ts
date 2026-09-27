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

export interface CoachSummary {
  biggest_mistake: string;
  best_decision: string;
  what_to_change: string;
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
  coach_summary?: CoachSummary;
  community_stat?: CommunityStat;
  audio_url?: string;
  rent?: RentSummary;
  solana_tx_url?: string;
}

export interface ApiError extends Error {
  status: number;
  message: string;
}

export interface SimulationCreateResponse {
  simulation_id: string;
  state: SimulationState;
}

export interface Fact {
  id: string;
  label: string;
  value_num: number | null;
  unit?: string;
  source?: string;
  note?: string;
}

export interface PoweredBy {
  snowflake_configured: boolean;
  cortex_model: string | null;
  embed_model: string | null;
  rag_enabled: boolean;
  vector_search: boolean;
  facts_count: number;
  data_credit: string;
  gemini_backup: boolean;
}

export interface SuggestedQuestion {
  id: string;
  question: string;
}

export interface LastRun {
  simulation_id: string;
  status: "active" | "completed";
  stage: string;
  outcome: string | null;
  overall_score: number;
  preparedness_gaps: string[];
  action_identifiers: string[];
}

export interface AssistantIntro {
  emergency_notice: string;
  powered_by: PoweredBy;
  location_label: string;
  area_notes: string[];
  facts: Fact[];
  facts_updated_at: string | null;
  facts_source: "snowflake-live" | "cache" | "none";
  last_run: LastRun | null;
  suggested_questions: SuggestedQuestion[];
}

export interface ChatTurn {
  role: "user" | "assistant";
  content: string;
}

export interface RetrievedChunk {
  id: string;
  source: string;
  score: number;
}

export interface AiMeta {
  provider: "snowflake-cortex-rag" | "snowflake-cortex" | "gemini";
  model: string;
  embed_model: string | null;
  retrieved: RetrievedChunk[];
  latency_ms: number;
  sql_statement: string | null;
  number_check: "passed" | "failed";
}

export interface AskResponse {
  kind: "emergency" | "verified" | "ai" | "fallback" | "greeting";
  answer: string;
  question_id: string | null;
  sources: string[];
  note: string | null;
  ai_meta: AiMeta | null;
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
  source: string;
}

export interface QuizResponse {
  title: string;
  disclaimer: string;
  questions: QuizQuestion[];
}

export interface EvacuationRoute {
  available: boolean;
  origin_label: string | null;
  shelter_name: string | null;
  shelter_area: string | null;
  transport_mode: string | null;
  distance_km: number | null;
  duration_min: number | null;
  feasibility: "clear" | "compromised" | null;
  warning: string | null;
  note: string;
}
