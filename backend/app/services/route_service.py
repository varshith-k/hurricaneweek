import json
import logging
import math
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SHELTERS_PATH = Path(__file__).resolve().parents[1] / "data" / "evacuation_shelters.json"

# Illustrative fixed starting point for the route check - the app doesn't
# collect a player's real address, so every run measures from the same
# representative Miami-Dade origin. Downtown Miami / Government Center.
ORIGIN_LON = -80.1937
ORIGIN_LAT = 25.7743
ORIGIN_LABEL = "Downtown Miami (illustrative starting point)"

# ORS has no moped/scooter profile. cycling-regular avoids highways and
# assumes a lower speed, a reasonable proxy for a scooter's real
# constraints. public_transit has no GTFS routing available here, so it
# falls back to a walking baseline, labeled clearly as illustrative.
PROFILE_BY_TRANSPORT = {
    "car": "driving-car",
    "scooter": "cycling-regular",
    "public_transit": "foot-walking",
}

# Flood risk above this, plus a non-car transport mode, means a real risk of
# the route being unsafe or impassable well before landfall.
COMPROMISED_FLOOD_RISK = 0.6


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


class RouteService:
    def __init__(self) -> None:
        self.api_key = os.getenv("ORS_API_KEY")
        self.enabled = bool(self.api_key)
        self.shelters = json.loads(SHELTERS_PATH.read_text(encoding="utf-8")) if self.enabled else []

    def _nearest_shelter(self) -> dict | None:
        if not self.shelters:
            return None
        return min(self.shelters, key=lambda s: _haversine_km(ORIGIN_LON, ORIGIN_LAT, s["lon"], s["lat"]))

    def evacuation_route(self, transport_type: str, flood_risk: float) -> dict:
        if not self.enabled:
            return {"available": False, "note": "Evacuation route lookup is not configured."}

        shelter = self._nearest_shelter()
        if shelter is None:
            return {"available": False, "note": "No shelter data available."}

        profile = PROFILE_BY_TRANSPORT.get(transport_type, "driving-car")

        try:
            response = httpx.post(
                f"https://api.openrouteservice.org/v2/directions/{profile}",
                headers={"Authorization": self.api_key, "Content-Type": "application/json"},
                json={"coordinates": [[ORIGIN_LON, ORIGIN_LAT], [shelter["lon"], shelter["lat"]]]},
                timeout=8.0,
            )
            response.raise_for_status()
            summary = response.json()["routes"][0]["summary"]
            distance_km = round(summary["distance"] / 1000, 1)
            duration_min = round(summary["duration"] / 60, 1)
        except Exception:  # noqa: BLE001 - route lookup is a helper, never break the evacuation decision
            logger.warning("Evacuation route lookup failed")
            return {"available": False, "note": "Could not reach the routing service right now."}

        compromised = transport_type != "car" and flood_risk >= COMPROMISED_FLOOD_RISK
        feasibility = "compromised" if compromised else "clear"
        warning = (
            f"Rising flood risk may make this {('scooter' if transport_type == 'scooter' else 'transit/walking')} "
            "route unsafe before landfall - consider leaving earlier or arranging a car."
            if compromised
            else None
        )

        return {
            "available": True,
            "origin_label": ORIGIN_LABEL,
            "shelter_name": shelter["name"],
            "shelter_area": shelter["area"],
            "transport_mode": profile,
            "distance_km": distance_km,
            "duration_min": duration_min,
            "feasibility": feasibility,
            "warning": warning,
            "note": "Illustrative route from a fixed starting point to a Miami-Dade shelter location, not a real-time evacuation order.",
        }
