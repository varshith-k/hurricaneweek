export const actionIdentifierText: Record<string, string> = {
  create_evacuation_trigger_plan:
    "Decide in advance what will make you leave and where you'll go. A nearby safe place on higher ground often beats a long drive.",
  add_elevated_scooter_storage:
    "Before a storm, bring your scooter indoors and off the floor. Flood water can destroy its battery.",
  verify_insurance_documents:
    "Check what your policy actually covers (renters insurance generally excludes flooding) and keep photos of your belongings.",
  maintain_3_day_water_supply:
    "Keep at least a 7-day water supply (about 1 gallon per person per day).",
  maintain_3_day_food_supply:
    "Keep at least a 7-day supply of non-perishable food.",
};

export function getActionText(identifier: string): string {
  return actionIdentifierText[identifier] ?? identifier.replace(/_/g, " ");
}
