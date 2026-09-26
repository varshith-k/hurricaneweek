from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.schemas.decision import DecisionOutcome
from app.schemas.event import EventChoice, EventResponse
from app.schemas.simulation import PlayerProfile, ScoreState, SimulationState


OutcomeType = Literal["good", "neutral", "bad"]


@dataclass(frozen=True)
class ChoiceRule:
    choice_id: str
    label: str
    cost: int
    readiness_delta: int
    risk_delta: int
    outcome_type: OutcomeType
    consequence: str


@dataclass(frozen=True)
class EventDefinition:
    event_id: str
    day_index: int
    title: str
    description: str
    choices: tuple[ChoiceRule, ...]


SIMULATION_EVENTS: tuple[EventDefinition, ...] = (
    EventDefinition(
        event_id="t120_supply_run",
        day_index=0,
        title="T-120h: Prepare Core Supplies",
        description="You have limited time before conditions worsen. Choose your supply strategy.",
        choices=(
            ChoiceRule(
                choice_id="full_kit",
                label="Buy full emergency kit",
                cost=120,
                readiness_delta=22,
                risk_delta=-8,
                outcome_type="good",
                consequence="You secure water, food, and batteries early.",
            ),
            ChoiceRule(
                choice_id="partial_kit",
                label="Buy partial supplies",
                cost=60,
                readiness_delta=10,
                risk_delta=-3,
                outcome_type="neutral",
                consequence="You cover basics, but shortages remain possible.",
            ),
            ChoiceRule(
                choice_id="skip",
                label="Wait and buy later",
                cost=0,
                readiness_delta=-5,
                risk_delta=8,
                outcome_type="bad",
                consequence="You risk shortages as stores become crowded.",
            ),
        ),
    ),
    EventDefinition(
        event_id="t96_property_protection",
        day_index=1,
        title="T-96h: Property Protection",
        description="Forecast confidence increases. Protect your home and transport.",
        choices=(
            ChoiceRule(
                choice_id="sandbags_and_secure",
                label="Buy sandbags and secure belongings",
                cost=80,
                readiness_delta=18,
                risk_delta=-6,
                outcome_type="good",
                consequence="You reduce flood exposure around key entry points.",
            ),
            ChoiceRule(
                choice_id="minimal_secure",
                label="Do minimal preparation",
                cost=30,
                readiness_delta=7,
                risk_delta=-1,
                outcome_type="neutral",
                consequence="You reduce some risk, but weak points remain.",
            ),
            ChoiceRule(
                choice_id="no_action",
                label="Take no action",
                cost=0,
                readiness_delta=-4,
                risk_delta=7,
                outcome_type="bad",
                consequence="Unprotected assets remain exposed to storm impact.",
            ),
        ),
    ),
    EventDefinition(
        event_id="t72_evacuation_plan",
        day_index=2,
        title="T-72h: Evacuation Decision",
        description="Authorities issue guidance. Decide how to move your household.",
        choices=(
            ChoiceRule(
                choice_id="evacuate_early",
                label="Evacuate early",
                cost=90,
                readiness_delta=20,
                risk_delta=-10,
                outcome_type="good",
                consequence="You avoid congestion and secure safer shelter.",
            ),
            ChoiceRule(
                choice_id="shelter_nearby",
                label="Use nearby shelter",
                cost=40,
                readiness_delta=12,
                risk_delta=-4,
                outcome_type="neutral",
                consequence="You improve safety but face local storm stress.",
            ),
            ChoiceRule(
                choice_id="stay_home",
                label="Stay home",
                cost=0,
                readiness_delta=-8,
                risk_delta=12,
                outcome_type="bad",
                consequence="Household remains directly exposed to severe conditions.",
            ),
        ),
    ),
    EventDefinition(
        event_id="t48_final_prep",
        day_index=3,
        title="T-48h: Final Preparations",
        description="Weather degrades quickly. Make final safety adjustments.",
        choices=(
            ChoiceRule(
                choice_id="final_lockdown",
                label="Complete final lockdown",
                cost=35,
                readiness_delta=12,
                risk_delta=-5,
                outcome_type="good",
                consequence="Critical devices are charged and essentials are secured.",
            ),
            ChoiceRule(
                choice_id="partial_lockdown",
                label="Partial final prep",
                cost=15,
                readiness_delta=5,
                risk_delta=-2,
                outcome_type="neutral",
                consequence="You mitigate some hazards but leave important gaps.",
            ),
            ChoiceRule(
                choice_id="no_final_prep",
                label="No additional prep",
                cost=0,
                readiness_delta=-3,
                risk_delta=6,
                outcome_type="bad",
                consequence="Remaining hazards carry directly into landfall.",
            ),
        ),
    ),
    EventDefinition(
        event_id="t24_landfall_response",
        day_index=4,
        title="T-24h: Landfall Response",
        description="Severe weather arrives. Choose immediate response behavior.",
        choices=(
            ChoiceRule(
                choice_id="strict_safety_protocol",
                label="Follow strict safety protocol",
                cost=10,
                readiness_delta=8,
                risk_delta=-8,
                outcome_type="good",
                consequence="You reduce injury and critical-loss exposure.",
            ),
            ChoiceRule(
                choice_id="basic_response",
                label="Follow basic guidance",
                cost=0,
                readiness_delta=3,
                risk_delta=-3,
                outcome_type="neutral",
                consequence="You maintain moderate safety during peak storm impact.",
            ),
            ChoiceRule(
                choice_id="panic_actions",
                label="Take risky reactive actions",
                cost=0,
                readiness_delta=-6,
                risk_delta=10,
                outcome_type="bad",
                consequence="Unplanned actions increase danger and losses.",
            ),
        ),
    ),
)


@dataclass
class SimulationRecord:
    simulation_id: UUID
    player_profile: PlayerProfile
    current_event_index: int
    cash_remaining: int
    preparedness_points: int
    risk_points: int
    created_at: datetime


class InMemorySimulationStore:
    def __init__(self) -> None:
        self._data: dict[UUID, SimulationRecord] = {}
        self._lock = Lock()

    def create(self, player_profile: PlayerProfile) -> SimulationRecord:
        simulation_id = uuid4()
        record = SimulationRecord(
            simulation_id=simulation_id,
            player_profile=player_profile,
            current_event_index=0,
            cash_remaining=player_profile.cash_on_hand,
            preparedness_points=20,
            risk_points=20,
            created_at=datetime.now(UTC),
        )
        with self._lock:
            self._data[simulation_id] = record
        return record

    def get(self, simulation_id: UUID) -> SimulationRecord:
        with self._lock:
            record = self._data.get(simulation_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Simulation not found")
        return record

    def save(self, record: SimulationRecord) -> None:
        with self._lock:
            self._data[record.simulation_id] = record


class SimulationEngine:
    def __init__(self, store: InMemorySimulationStore) -> None:
        self.store = store

    def create_simulation(self, player_profile: PlayerProfile) -> SimulationRecord:
        return self.store.create(player_profile)

    def get_current_event(self, simulation_id: UUID) -> EventResponse:
        record = self.store.get(simulation_id)
        if record.current_event_index >= len(SIMULATION_EVENTS):
            return EventResponse(
                simulation_id=simulation_id,
                event_id="simulation_complete",
                day_index=5,
                title="Simulation Complete",
                description="No more events remain.",
                choices=[],
                simulation_complete=True,
            )

        event = SIMULATION_EVENTS[record.current_event_index]
        return EventResponse(
            simulation_id=simulation_id,
            event_id=event.event_id,
            day_index=event.day_index,
            title=event.title,
            description=event.description,
            choices=[
                EventChoice(choice_id=choice.choice_id, label=choice.label, cost=choice.cost)
                for choice in event.choices
            ],
            simulation_complete=False,
        )

    def apply_decision(self, simulation_id: UUID, event_id: str, choice_id: str) -> tuple[DecisionOutcome, SimulationState]:
        record = self.store.get(simulation_id)

        if record.current_event_index >= len(SIMULATION_EVENTS):
            raise HTTPException(status_code=409, detail="Simulation already complete")

        event = SIMULATION_EVENTS[record.current_event_index]
        if event.event_id != event_id:
            raise HTTPException(status_code=400, detail="Decision event does not match current event")

        selected_choice = next((choice for choice in event.choices if choice.choice_id == choice_id), None)
        if selected_choice is None:
            raise HTTPException(status_code=400, detail="Invalid choice for event")
        if selected_choice.cost > record.cash_remaining:
            raise HTTPException(status_code=400, detail="Insufficient cash for selected choice")

        record.cash_remaining -= selected_choice.cost
        record.preparedness_points = max(0, record.preparedness_points + selected_choice.readiness_delta)
        record.risk_points = max(0, record.risk_points + selected_choice.risk_delta)
        record.current_event_index += 1
        self.store.save(record)

        outcome = DecisionOutcome(
            consequence=selected_choice.consequence,
            readiness_delta=selected_choice.readiness_delta,
            risk_delta=selected_choice.risk_delta,
            cash_delta=-selected_choice.cost,
        )
        return outcome, self._build_state(record)

    def get_state(self, simulation_id: UUID) -> SimulationState:
        return self._build_state(self.store.get(simulation_id))

    def _build_state(self, record: SimulationRecord) -> SimulationState:
        scores = self._compute_scores(record)
        is_complete = record.current_event_index >= len(SIMULATION_EVENTS)
        return SimulationState(
            day_index=min(record.current_event_index, 5),
            simulation_complete=is_complete,
            cash_remaining=record.cash_remaining,
            preparedness_points=record.preparedness_points,
            risk_points=record.risk_points,
            scores=scores,
        )

    def _compute_scores(self, record: SimulationRecord) -> ScoreState:
        safety = max(0, min(100, 100 - int(record.risk_points * 1.4)))

        starting_cash = max(1, record.player_profile.cash_on_hand)
        financial = max(0, min(100, int((record.cash_remaining / starting_cash) * 100)))

        preparedness = max(0, min(100, int(record.preparedness_points * 1.6)))

        event_progress = min(record.current_event_index, len(SIMULATION_EVENTS))
        timing_raw = (event_progress * 15) + (record.preparedness_points - record.risk_points)
        timing = max(0, min(100, int(50 + timing_raw / 2)))

        return ScoreState(
            safety=safety,
            financial=financial,
            preparedness=preparedness,
            timing=timing,
        )

