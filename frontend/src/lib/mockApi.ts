import type {
  DecisionResponse,
  EventResponse,
  FinalReport,
  PlayerProfile,
  SimulationCreateResponse,
  SimulationState,
} from "@/lib/types";

const baseStageFlow = [
  "T_MINUS_120",
  "T_MINUS_96",
  "T_MINUS_72",
  "T_MINUS_48",
  "T_MINUS_24",
  "LANDFALL",
  "RECOVERY",
] as const;

const eventTemplates: Array<{
  event_id: string;
  stage: string;
  title: string;
  description: string;
  choices: Array<{ choice_id: string; label: string; cost?: number; hours?: number; cash_delta?: number; consequence: string }>;
}> = [
  {
    event_id: "supply_run",
    stage: "T_MINUS_120",
    title: "Early Supply Run",
    description: "You can still shop before shortages begin.",
    choices: [
      { choice_id: "buy_early_supplies", label: "Buy 5 days of supplies now", cost: 120, cash_delta: -120, consequence: "You secure food and water before shelves thin out." },
      { choice_id: "buy_partial_supplies", label: "Buy only basic supplies", cost: 65, cash_delta: -65, consequence: "You reduce some risk but remain understocked." },
      { choice_id: "delay_shopping", label: "Delay shopping", consequence: "You risk shortages and panic buying later." },
    ],
  },
  {
    event_id: "scooter_protection",
    stage: "T_MINUS_96",
    title: "Scooter and Property Protection",
    description: "Flooding could damage uncovered transport and valuables.",
    choices: [
      { choice_id: "protect_scooter_and_docs", label: "Move scooter to safe storage and secure documents", cost: 45, cash_delta: -45, consequence: "You reduce flood damage and secure critical paperwork." },
      { choice_id: "secure_documents_only", label: "Secure documents only", cost: 15, cash_delta: -15, consequence: "Documents are safer, but scooter remains exposed." },
      { choice_id: "do_nothing", label: "Do nothing", consequence: "Exposure remains high as flood risk increases." },
    ],
  },
  {
    event_id: "work_vs_prepare",
    stage: "T_MINUS_72",
    title: "Work Shift vs Preparation",
    description: "You can work extra hours or spend the time preparing.",
    choices: [
      { choice_id: "skip_shift_prepare", label: "Skip shift and prepare", cost: 30, cash_delta: -30, consequence: "You sacrifice income for better readiness." },
      { choice_id: "work_shift", label: "Work the shift", cost: -60, cash_delta: 60, consequence: "You gain cash but lose preparation time." },
    ],
  },
  {
    event_id: "insurance_verification",
    stage: "T_MINUS_48",
    title: "Insurance Verification",
    description: "Verify your policy and gather claim-ready documentation.",
    choices: [
      { choice_id: "verify_insurance", label: "Verify policy and take inventory photos", consequence: "You improve claim readiness and reduce uncertainty." },
      { choice_id: "skip_verification", label: "Skip verification", consequence: "Coverage details remain unclear." },
    ],
  },
  {
    event_id: "evacuation_choice",
    stage: "T_MINUS_24",
    title: "Evacuation Decision",
    description: "Road conditions are worsening. Decide your response.",
    choices: [
      { choice_id: "evacuate_early", label: "Evacuate before roads congest", cost: 90, cash_delta: -90, consequence: "You move to safer ground before peak risk." },
      { choice_id: "shelter_locally", label: "Move to nearby shelter", cost: 40, cash_delta: -40, consequence: "You reduce risk but remain near storm impacts." },
      { choice_id: "stay_put", label: "Stay in place", consequence: "You remain in the highest-risk zone." },
    ],
  },
  {
    event_id: "landfall_response",
    stage: "LANDFALL",
    title: "Landfall Response",
    description: "Peak storm arrives. Your immediate behavior matters.",
    choices: [
      { choice_id: "strict_protocol", label: "Follow strict emergency protocol", cost: 10, cash_delta: -10, consequence: "You minimize avoidable risk during peak impact." },
      { choice_id: "panic_actions", label: "Take unplanned reactive actions", cost: 5, cash_delta: -5, consequence: "Reactive choices increase exposure and losses." },
    ],
  },
  {
    event_id: "recovery_decision",
    stage: "RECOVERY",
    title: "Recovery Decision",
    description: "Choose immediate post-storm actions.",
    choices: [
      { choice_id: "document_damage_and_plan", label: "Document damage and start recovery plan", cost: 20, cash_delta: -20, consequence: "Structured recovery reduces long-term disruption." },
      { choice_id: "delay_recovery_actions", label: "Delay recovery actions", consequence: "Delays increase preventable setbacks." },
    ],
  },
];

const labels = eventTemplates.reduce<Record<string, Record<string, string>>>((acc, event) => {
  acc[event.event_id] = Object.fromEntries(event.choices.map((choice) => [choice.choice_id, choice.label]));
  return acc;
}, {});

function createMockState(profile: PlayerProfile): SimulationState {
  const stageIndex = 0;
  const windMap: Record<string, number> = {
    T_MINUS_120: 25,
    T_MINUS_96: 35,
    T_MINUS_72: 50,
    T_MINUS_48: 65,
    T_MINUS_24: 85,
    LANDFALL: 105,
    RECOVERY: 35,
  };
  const floodMap: Record<string, number> = {
    T_MINUS_120: 0.1,
    T_MINUS_96: 0.2,
    T_MINUS_72: 0.35,
    T_MINUS_48: 0.5,
    T_MINUS_24: 0.7,
    LANDFALL: 0.85,
    RECOVERY: 0.25,
  };

  const stage = baseStageFlow[stageIndex];
  return {
    stage,
    status: "active",
    simulation_complete: false,
    cash: profile.cash_on_hand,
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
    storm: {
      stage,
      wind_mph: windMap[stage],
      flood_risk: floodMap[stage],
    },
    scores: {
      safety: 60,
      financial: 60,
      preparedness: 60,
      timing: 60,
      overall: 60,
    },
  };
}

export async function mockHealthCheck(): Promise<{ status: string }> {
  return { status: "ok" };
}

export async function mockCreateSimulation(profile: PlayerProfile): Promise<SimulationCreateResponse> {
  return {
    simulation_id: "mock-simulation-id",
    state: createMockState(profile),
  };
}

export async function mockGetCurrentEvent(simulationId: string): Promise<EventResponse> {
  const stage = baseStageFlow[0];
  const template = eventTemplates.find((event) => event.stage === stage) ?? eventTemplates[0];
  return {
    simulation_id: simulationId,
    event_id: template.event_id,
    stage: template.stage,
    title: template.title,
    description: template.description,
    choices: template.choices.map((choice) => ({
      choice_id: choice.choice_id,
      label: choice.label,
      cost: choice.cost,
      hours: choice.hours,
    })),
    simulation_complete: false,
    probability: 0.7,
    stage_label: "T−120h · Storm appears in the 5-day forecast",
    hours_to_landfall: 120,
  };
}

export async function mockSubmitDecision(simulationId: string, eventId: string, choiceId: string): Promise<DecisionResponse> {
  const template = eventTemplates.find((event) => event.event_id === eventId) ?? eventTemplates[0];
  const choice = template.choices.find((item) => item.choice_id === choiceId) ?? template.choices[0];

  const nextStageIndex = Math.min(baseStageFlow.indexOf(template.stage as (typeof baseStageFlow)[number]) + 1, baseStageFlow.length - 1);
  const nextEventTemplate = eventTemplates.find((event) => event.stage === baseStageFlow[nextStageIndex]) ?? eventTemplates[0];

  const response: DecisionResponse = {
    simulation_id: simulationId,
    status: nextStageIndex === baseStageFlow.length - 1 ? "completed" : "in_progress",
    outcome: {
      consequence: choice.consequence,
      cash_delta: choice.cash_delta ?? 0,
      preparedness_delta: 2,
      timing_delta: 2,
    },
    state: {
      ...createMockState({ cash_on_hand: 400, has_insurance: false, housing_type: "apartment", transport_type: "scooter", household_size: 1, needs_refrigerated_medication: false }),
      stage: nextEventTemplate.stage,
      status: nextStageIndex === baseStageFlow.length - 1 ? "completed" : "active",
      simulation_complete: nextStageIndex === baseStageFlow.length - 1,
      completed_events: [eventId],
      cash: Math.max(0, 400 + (choice.cash_delta ?? 0)),
      scores: { safety: 75, financial: 72, preparedness: 80, timing: 71, overall: 75 },
      storm: { stage: nextEventTemplate.stage, wind_mph: 35, flood_risk: 0.3 },
    },
    next_event: nextStageIndex === baseStageFlow.length - 1 ? null : {
      simulation_id: simulationId,
      event_id: nextEventTemplate.event_id,
      stage: nextEventTemplate.stage,
      title: nextEventTemplate.title,
      description: nextEventTemplate.description,
      choices: nextEventTemplate.choices.map((item) => ({ choice_id: item.choice_id, label: item.label })),
      simulation_complete: false,
      probability: 0.75,
      stage_label: "T−96h · Preparation window",
    },
    final_report: nextStageIndex === baseStageFlow.length - 1 ? {
      simulation_id: simulationId,
      outcome: "Well Prepared",
      scores: { safety: 78, financial: 74, preparedness: 82, timing: 76, overall: 78 },
      financial_summary: { starting_cash: 400, ending_cash: 330, damage: 120 },
      strengths: ["You planned ahead for supplies and protection."],
      preparedness_gaps: ["A plan for evacuation timing would reduce risk."],
      action_identifiers: ["create_evacuation_trigger_plan", "maintain_3_day_water_supply"],
      decision_history: [{ stage: template.stage, event_id: template.event_id, choice_id: choiceId, consequence: choice.consequence }],
      insurance_breakdown: [{ item: "Renters coverage", cause: "Water intrusion", covered: false, deductible: 500, payout: 0, reason: "Flood damage is not generally covered by renters policies." }],
      decision_quality: [{ stage: template.stage, probability: 0.8, options: [{ label: choice.label, expected_loss: 120, chosen: true }] }],
      plan_text: "Build a simple leave plan with a backup shelter and a check-in trigger for the next storm.",
      community_stat: { text: "Based on 23 players", count: 23 },
      audio_url: "https://example.com/simulated-radio.mp3",
      rent: { owed: 1100, paid: true, late_fee: 0 },
    } : null,
  };

  return response;
}

export async function mockGetFinalReport(simulationId: string): Promise<FinalReport> {
  return {
    simulation_id: simulationId,
    outcome: "Well Prepared",
    scores: { safety: 78, financial: 74, preparedness: 82, timing: 76, overall: 78 },
    financial_summary: { starting_cash: 400, ending_cash: 330, damage: 120 },
    strengths: ["You planned ahead for supplies and protection."],
    preparedness_gaps: ["A plan for evacuation timing would reduce risk."],
    action_identifiers: ["create_evacuation_trigger_plan", "maintain_3_day_water_supply"],
    decision_history: [{ stage: "T_MINUS_120", event_id: "supply_run", choice_id: "buy_early_supplies", consequence: "You secure food and water before shelves thin out." }],
    insurance_breakdown: [{ item: "Renters coverage", cause: "Water intrusion", covered: false, deductible: 500, payout: 0, reason: "Flood damage is not generally covered by renters policies." }],
    decision_quality: [{ stage: "T_MINUS_120", probability: 0.8, options: [{ label: "Buy 5 days of supplies now", expected_loss: 120, chosen: true }] }],
    plan_text: "Build a simple leave plan with a backup shelter and a check-in trigger for the next storm.",
    community_stat: { text: "Based on 23 players", count: 23 },
    audio_url: "https://example.com/simulated-radio.mp3",
    rent: { owed: 1100, paid: true, late_fee: 0 },
  };
}

export const mockChoiceLookup = labels;
