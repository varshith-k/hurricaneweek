import logging
import os
from uuid import UUID

from app.services.assistant_service import AssistantService
from app.services.audio_service import AudioService
from app.services.mongo_store import MongoSimulationStore
from app.services.plan_service import PlanService
from app.services.route_service import RouteService
from app.services.scoring_engine import build_strengths_and_gaps, compute_scores
from app.services.simulation_engine import InMemorySimulationStore, SimulationEngine
from app.services.snowflake_service import FactsRepository
from app.services.solana_service import SolanaService
from app.services.tiger_service import TigerService

logger = logging.getLogger(__name__)

_mongodb_uri = os.getenv("MONGODB_URI")
if _mongodb_uri:
    try:
        simulation_store = MongoSimulationStore(_mongodb_uri)
        simulation_store.ping()
        logger.info("Using MongoDB-backed simulation store")
    except Exception as exc:  # noqa: BLE001 - fall back rather than fail startup
        logger.warning("MongoDB unreachable (%s), falling back to in-memory simulation store", exc)
        simulation_store = InMemorySimulationStore()
else:
    simulation_store = InMemorySimulationStore()

tiger_service = TigerService()
audio_service = AudioService()
plan_service = PlanService()
solana_service = SolanaService()
route_service = RouteService()
simulation_engine = SimulationEngine(
    store=simulation_store,
    tiger_service=tiger_service,
    audio_service=audio_service,
    plan_service=plan_service,
    solana_service=solana_service,
)


def get_simulation_engine() -> SimulationEngine:
    return simulation_engine


def _last_run_loader(simulation_id: UUID) -> dict | None:
    state = simulation_store.get(simulation_id)
    scores = state.get("final_scores") or compute_scores(state)
    outcome = state.get("final_outcome") if state["status"] == "completed" else None
    _, gaps, actions = build_strengths_and_gaps(state)
    return {
        "simulation_id": simulation_id,
        "status": state["status"],
        "stage": state["stage"],
        "outcome": outcome,
        "overall_score": scores["overall"],
        "preparedness_gaps": gaps,
        "action_identifiers": actions,
    }


facts_repository = FactsRepository()
assistant_service = AssistantService(facts=facts_repository, last_run_loader=_last_run_loader)
simulation_engine.real_world_context_loader = assistant_service.real_world_context
