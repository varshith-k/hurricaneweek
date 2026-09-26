
def apply_choice_effects(state: dict, choice: dict) -> None:
    state["cash"] = max(0, state["cash"] + choice.get("cash_delta", 0))
    state["food_days"] = max(0, state["food_days"] + choice.get("food_days_delta", 0))
    state["water_days"] = max(0, state["water_days"] + choice.get("water_days_delta", 0))
    state["preparedness_points"] = max(0, state["preparedness_points"] + choice.get("preparedness_delta", 0))
    state["timing_points"] = max(0, state["timing_points"] + choice.get("timing_delta", 0))

    for flag_name, flag_value in choice.get("set_flags", {}).items():
        state[flag_name] = flag_value


def apply_delayed_consequences(state: dict) -> None:
    flood_risk = state["storm"]["flood_risk"]

    if state["player_profile"]["transport_type"] == "scooter" and (not state["scooter_protected"]) and flood_risk > 0.70:
        state["financial_loss"] += 220

    if not state["evacuated"] and flood_risk > 0.80:
        state["safety_penalty"] += 45

    if state["food_days"] < 3:
        state["financial_loss"] += 60
        state["preparedness_points"] = max(0, state["preparedness_points"] - 6)

    if state["water_days"] < 3:
        state["financial_loss"] += 80
        state["preparedness_points"] = max(0, state["preparedness_points"] - 8)

    if not state["documents_secured"]:
        state["financial_loss"] += 50

    if not state["insurance_verified"] and state["player_profile"]["has_insurance"]:
        state["financial_loss"] += 40

    state["cash"] = max(0, state["cash"] - state["financial_loss"])
