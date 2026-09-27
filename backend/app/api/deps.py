from app.services.audio_service import AudioService
from app.services.plan_service import PlanService
from app.services.simulation_engine import InMemorySimulationStore, SimulationEngine
from app.services.solana_service import SolanaService
from app.services.tiger_service import TigerService

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
