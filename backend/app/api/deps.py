import logging
import os

from app.services.audio_service import AudioService
from app.services.mongo_store import MongoSimulationStore
from app.services.plan_service import PlanService
from app.services.simulation_engine import InMemorySimulationStore, SimulationEngine
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
simulation_engine = SimulationEngine(
    store=simulation_store,
    tiger_service=tiger_service,
    audio_service=audio_service,
    plan_service=plan_service,
    solana_service=solana_service,
)


def get_simulation_engine() -> SimulationEngine:
    return simulation_engine
