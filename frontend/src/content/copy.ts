export const disclaimer = "Educational simulation. Not an emergency warning system or an insurance coverage determination.";

export const introText =
  "Hurricane Week is a personal disaster-readiness simulator built to help you test choices before a storm arrives. You will make decisions through the week, watch how your plan holds up, and review the full report after the storm passes.";

export const safetyGateNotice =
  "Your safety score fell into the critical range. No amount of money saved offsets a life-threatening decision.";

export const floodRiskTooltip = "A scenario parameter, not a real forecast.";

export const stageIntroCopy = {
  setupTitle: "Hurricane Week",
  setupTagline: "A realistic readiness simulator for a storm week.",
};

export const stageSituationCopy: Record<string, string> = {
  T_MINUS_120: "You have time on your side, but only if you use it.", // VERIFY
  T_MINUS_96: "You can still protect the things that would be hardest to replace.", // VERIFY
  T_MINUS_72: "Your next choice trades preparation time against immediate income.", // VERIFY
  T_MINUS_48: "The forecast is narrowing; uncertainty is becoming a cost.", // VERIFY
  T_MINUS_24: "Roads and options are tightening around you.", // VERIFY
  LANDFALL: "The storm is here. Your earlier choices now meet the conditions.", // VERIFY
  RECOVERY: "The wind has eased, and the next work is documenting what happened.", // VERIFY
};

export const generalCopy = {
  simulatedBadge: "Simulated",
  emergencyRadioLabel: "Simulated emergency radio",
  backendStatusOnline: "Engine online",
  backendStatusOffline: "Offline — demo mode available",
  retryLabel: "Retry",
  startOverLabel: "Start over",
};

export const verifyCopy = `// VERIFY: Educational copy beyond the provided backend contract and game prompt.`;
