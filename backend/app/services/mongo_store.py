import logging
from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException
from pymongo import MongoClient

from app.schemas.simulation import PlayerProfile
from app.services.event_engine import STAGES, get_storm_for_stage

logger = logging.getLogger(__name__)


class MongoSimulationStore:
    """Persists simulation state in MongoDB Atlas instead of a process-local dict.

    Same interface as InMemorySimulationStore, so it survives backend
    restarts/redeploys - previously, every deploy silently wiped any
    simulation in progress.
    """

    def __init__(self, uri: str, db_name: str = "hurricaneweek") -> None:
        self._client: MongoClient = MongoClient(uri, uuidRepresentation="standard", serverSelectionTimeoutMS=5000)
        self._collection = self._client[db_name]["simulations"]

    def ping(self) -> None:
        self._client.admin.command("ping")

    def create(self, player_profile: PlayerProfile) -> dict:
        simulation_id = uuid4()
        initial_stage = STAGES[0]
        state: dict = {
            "_id": simulation_id,
            "simulation_id": simulation_id,
            "status": "active",
            "stage": initial_stage,
            "starting_cash": player_profile.cash_on_hand,
            "cash": player_profile.cash_on_hand,
            "food_days": 1,
            "water_days": 1,
            "evacuated": False,
            "scooter_protected": False,
            "documents_secured": False,
            "insurance_verified": False,
            "transport_available": True,
            "preparedness_points": 0,
            "timing_points": 0,
            "safety_penalty": 0,
            "financial_loss": 0,
            "completed_events": [],
            "decision_history": [],
            "player_profile": player_profile.model_dump(),
            "storm": get_storm_for_stage(initial_stage),
            "created_at": datetime.now(UTC).isoformat(),
        }
        self._collection.insert_one(dict(state))
        return {key: value for key, value in state.items() if key != "_id"}

    def get(self, simulation_id: UUID) -> dict:
        doc = self._collection.find_one({"_id": simulation_id})
        if doc is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        doc.pop("_id", None)
        return doc

    def save(self, simulation_id: UUID, state: dict) -> None:
        doc = dict(state)
        doc["_id"] = simulation_id
        self._collection.replace_one({"_id": simulation_id}, doc, upsert=True)
