import json
from pathlib import Path
from typing import Any

from fastapi import HTTPException

STAGES = [
    "T_MINUS_120",
    "T_MINUS_96",
    "T_MINUS_72",
    "T_MINUS_48",
    "T_MINUS_24",
    "LANDFALL",
    "RECOVERY",
]

STORM_BY_STAGE = {
    "T_MINUS_120": {"wind_mph": 25, "flood_risk": 0.10},
    "T_MINUS_96": {"wind_mph": 35, "flood_risk": 0.20},
    "T_MINUS_72": {"wind_mph": 50, "flood_risk": 0.35},
    "T_MINUS_48": {"wind_mph": 65, "flood_risk": 0.50},
    "T_MINUS_24": {"wind_mph": 85, "flood_risk": 0.70},
    "LANDFALL": {"wind_mph": 105, "flood_risk": 0.85},
    "RECOVERY": {"wind_mph": 35, "flood_risk": 0.25},
}


def load_event_templates() -> list[dict[str, Any]]:
    template_path = Path(__file__).resolve().parent.parent / "data" / "event_templates.json"
    with template_path.open("r", encoding="utf-8-sig") as infile:
        return json.load(infile)


EVENT_TEMPLATES = load_event_templates()


def evaluate_eligibility(rule: str, state: dict[str, Any]) -> bool:
    if rule == "is_scooter_user":
        return state["player_profile"]["transport_type"] == "scooter"
    if rule == "not_scooter_user":
        return state["player_profile"]["transport_type"] != "scooter"
    if rule == "scooter_unprotected":
        return not state["scooter_protected"]
    if rule == "insurance_not_verified":
        return not state["insurance_verified"]
    if rule == "not_evacuated":
        return not state["evacuated"]
    if rule == "needs_refrigerated_medication":
        return state["player_profile"].get("needs_refrigerated_medication", False)
    raise HTTPException(status_code=500, detail=f"Unknown eligibility rule: {rule}")


def find_event_for_stage(state: dict[str, Any]) -> dict[str, Any]:
    current_stage = state["stage"]
    for event in EVENT_TEMPLATES:
        if event["stage"] != current_stage:
            continue
        if event["event_id"] in state["completed_events"]:
            continue
        eligibility_rules = event.get("eligibility", [])
        if all(evaluate_eligibility(rule, state) for rule in eligibility_rules):
            return event
    raise HTTPException(status_code=409, detail=f"No eligible event found for stage: {current_stage}")


def get_storm_for_stage(stage: str) -> dict[str, Any]:
    return STORM_BY_STAGE[stage]


def advance_stage(state: dict[str, Any]) -> None:
    current_index = STAGES.index(state["stage"])
    if current_index == len(STAGES) - 1:
        state["status"] = "completed"
        return
    state["stage"] = STAGES[current_index + 1]
