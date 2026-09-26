from app.services.simulation_engine import InMemorySimulationStore, SimulationEngine

simulation_store = InMemorySimulationStore()
simulation_engine = SimulationEngine(store=simulation_store)


def get_simulation_engine() -> SimulationEngine:
    return simulation_engine

