from copy import deepcopy
from datetime import UTC, datetime
from threading import Lock
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.schemas.decision import DecisionOutcome
from app.schemas.event import EventChoice, EventResponse
from app.schemas.report import FinalReport, FinancialSummary
from app.schemas.simulation import PlayerProfile, ScoreState, SimulationState, StormState
from app.services.consequence_engine import apply_choice_effects, apply_delayed_consequences
from app.services.event_engine import STAGES, advance_stage, find_event_for_stage, get_storm_for_stage
from app.services.scoring_engine import build_strengths_and_gaps, compute_scores, map_outcome


class InMemorySimulationStore:
    def __init__(self) -> None:
        self._data: dict[UUID, dict] = {}
        self._lock = Lock()

    def create(self, player_profile: PlayerProfile) -> dict:
        simulation_id = uuid4()
        initial_stage = STAGES[0]
        state: dict = {
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
        with self._lock:
            self._data[simulation_id] = state
        return deepcopy(state)

    def get(self, simulation_id: UUID) -> dict:
        with self._lock:
            state = self._data.get(simulation_id)
        if state is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return deepcopy(state)

    def save(self, simulation_id: UUID, state: dict) -> None:
        with self._lock:
            self._data[simulation_id] = deepcopy(state)


class SimulationEngine:
    def __init__(self, store: InMemorySimulationStore) -> None:
        self.store = store

    def create_simulation(self, player_profile: PlayerProfile) -> dict:
        return self.store.create(player_profile)

    def get_state(self, simulation_id: UUID) -> SimulationState:
        state = self.store.get(simulation_id)
        return self._build_state_response(state)

    def get_current_event(self, simulation_id: UUID) -> EventResponse:
        state = self.store.get(simulation_id)
        if state["status"] == "completed":
            return EventResponse(
                simulation_id=simulation_id,
                event_id="simulation_complete",
                stage=state["stage"],
                title="Simulation Complete",
                description="No more eligible events remain.",
                choices=[],
                simulation_complete=True,
            )

        event = find_event_for_stage(state)
        return EventResponse(
            simulation_id=simulation_id,
            event_id=event["event_id"],
            stage=event["stage"],
            title=event["title"],
            description=event["description"],
            choices=[EventChoice(choice_id=choice["choice_id"], label=choice["label"]) for choice in event["choices"]],
            simulation_complete=False,
        )

    def apply_decision(self, simulation_id: UUID, event_id: str, choice_id: str) -> tuple[DecisionOutcome, SimulationState]:
        state = self.store.get(simulation_id)
        if state["status"] != "active":
            raise HTTPException(status_code=409, detail="Simulation is already completed")

        event = find_event_for_stage(state)
        if event["event_id"] != event_id:
            raise HTTPException(status_code=400, detail="Decision event does not match current eligible event")
        if event_id in state["completed_events"]:
            raise HTTPException(status_code=409, detail="Event already completed")

        choice = next((item for item in event["choices"] if item["choice_id"] == choice_id), None)
        if choice is None:
            raise HTTPException(status_code=400, detail="Invalid choice for event")

        if state["cash"] + choice.get("cash_delta", 0) < 0:
            raise HTTPException(status_code=400, detail="Insufficient cash for selected choice")

        apply_choice_effects(state, choice)
        state["completed_events"].append(event_id)
        state["decision_history"].append(
            {
                "stage": state["stage"],
                "event_id": event_id,
                "choice_id": choice_id,
                "consequence": choice["consequence"],
            }
        )

        if state["stage"] == "LANDFALL":
            apply_delayed_consequences(state)

        advance_stage(state)
        state["storm"] = get_storm_for_stage(state["stage"])

        if state["status"] == "completed":
            scores = compute_scores(state)
            state["final_scores"] = scores
            state["final_outcome"] = map_outcome(scores)

        self.store.save(simulation_id, state)

        outcome = DecisionOutcome(
            consequence=choice["consequence"],
            preparedness_delta=choice.get("preparedness_delta", 0),
            timing_delta=choice.get("timing_delta", 0),
            cash_delta=choice.get("cash_delta", 0),
        )
        return outcome, self._build_state_response(state)

    def build_final_report(self, simulation_id: UUID) -> FinalReport:
        state = self.store.get(simulation_id)
        if state["status"] != "completed":
            raise HTTPException(status_code=409, detail="Simulation is not complete yet")

        scores = state.get("final_scores") or compute_scores(state)
        outcome = state.get("final_outcome") or map_outcome(scores)
        strengths, gaps, actions = build_strengths_and_gaps(state)

        return FinalReport(
            simulation_id=simulation_id,
            outcome=outcome,
            scores=ScoreState(**scores),
            financial_summary=FinancialSummary(
                starting_cash=state["starting_cash"],
                ending_cash=state["cash"],
                damage=state["financial_loss"],
            ),
            strengths=strengths,
            preparedness_gaps=gaps,
            action_identifiers=actions,
            decision_history=state["decision_history"],
        )

    def _build_state_response(self, state: dict) -> SimulationState:
        scores = compute_scores(state)
        return SimulationState(
            stage=state["stage"],
            status=state["status"],
            simulation_complete=state["status"] == "completed",
            cash=state["cash"],
            food_days=state["food_days"],
            water_days=state["water_days"],
            evacuated=state["evacuated"],
            scooter_protected=state["scooter_protected"],
            documents_secured=state["documents_secured"],
            insurance_verified=state["insurance_verified"],
            transport_available=state["transport_available"],
            preparedness_points=state["preparedness_points"],
            timing_points=state["timing_points"],
            financial_loss=state["financial_loss"],
            completed_events=state["completed_events"],
            storm=StormState(stage=state["stage"], **state["storm"]),
            scores=ScoreState(**scores),
        )
