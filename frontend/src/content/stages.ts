export const stageLabelMap: Record<string, string> = {
  T_MINUS_120: "T−120h · Storm appears in the 5-day forecast",
  T_MINUS_96: "T−96h · Preparation window",
  T_MINUS_72: "T−72h · Storm strengthening",
  T_MINUS_48: "T−48h · Hurricane Watch",
  T_MINUS_24: "T−24h · Hurricane Warning",
  LANDFALL: "Landfall",
  RECOVERY: "T+24h · Recovery",
};

export function getStageLabel(stage: string | undefined): string {
  if (!stage) return "Stage";
  return stageLabelMap[stage] ?? stage.replace(/_/g, " ");
}
