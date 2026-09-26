
def _clamp_score(value: float) -> int:
    return int(max(0, min(100, round(value))))


def compute_scores(state: dict) -> dict[str, int]:
    safety = 100
    if not state["evacuated"]:
        safety -= 25
    if state["stage"] in {"LANDFALL", "RECOVERY"} and not state["evacuated"]:
        safety -= 10
    if not state["transport_available"]:
        safety -= 10
    safety -= state["safety_penalty"]

    preparedness = 25
    preparedness += min(20, state["food_days"] * 4)
    preparedness += min(20, state["water_days"] * 4)
    preparedness += 8 if state["documents_secured"] else 0
    preparedness += 8 if state["scooter_protected"] else 0
    preparedness += 8 if state["insurance_verified"] else 0
    preparedness += 8 if state["evacuated"] else 0
    preparedness += min(20, max(0, state["preparedness_points"]))

    starting_cash = max(1, state["starting_cash"])
    financial = 100 - ((state["financial_loss"] / starting_cash) * 100)
    if state["cash"] <= 0:
        financial -= 10

    timing = 40 + state["timing_points"]
    if not state["evacuated"]:
        timing -= 10

    safety_score = _clamp_score(safety)
    financial_score = _clamp_score(financial)
    preparedness_score = _clamp_score(preparedness)
    timing_score = _clamp_score(timing)

    weighted = (
        (safety_score * 0.35)
        + (financial_score * 0.30)
        + (preparedness_score * 0.20)
        + (timing_score * 0.15)
    )

    overall = _clamp_score(weighted)
    return {
        "safety": safety_score,
        "financial": financial_score,
        "preparedness": preparedness_score,
        "timing": timing_score,
        "overall": overall,
    }


def map_outcome(scores: dict[str, int]) -> str:
    if scores["safety"] < 40:
        return "Critical Vulnerability"
    overall = scores["overall"]
    if overall >= 90:
        return "Highly Resilient"
    if overall >= 75:
        return "Well Prepared"
    if overall >= 60:
        return "Safe but Exposed"
    if overall >= 40:
        return "High Vulnerability"
    return "Critical Vulnerability"


def build_strengths_and_gaps(state: dict) -> tuple[list[str], list[str], list[str]]:
    strengths: list[str] = []
    gaps: list[str] = []
    actions: list[str] = []

    if state["evacuated"]:
        strengths.append("Evacuation plan executed")
    else:
        gaps.append("No evacuation completed")
        actions.append("create_evacuation_trigger_plan")

    if state["scooter_protected"]:
        strengths.append("Scooter/property protection completed")
    elif state["player_profile"]["transport_type"] == "scooter":
        gaps.append("Scooter remained flood-exposed")
        actions.append("add_elevated_scooter_storage")

    if state["insurance_verified"]:
        strengths.append("Insurance verification completed")
    else:
        gaps.append("Insurance status not verified")
        actions.append("verify_insurance_documents")

    if state["water_days"] < 3:
        gaps.append("Insufficient emergency water")
        actions.append("maintain_3_day_water_supply")

    if state["food_days"] < 3:
        gaps.append("Insufficient emergency food")
        actions.append("maintain_3_day_food_supply")

    if not strengths:
        strengths.append("Completed full simulation run")

    return strengths, gaps, actions
