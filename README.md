# Hurricane Week

An interactive hurricane-preparedness simulator. You play a Miami-Dade resident with $400 and five days before landfall — every decision (evacuate or shelter, insure or risk it, spend or save) changes your safety, finances, and outcome score. Built for ShellHacks/MLH 2026.

**Live: [hurricaneweek.miami](https://hurricaneweek.miami)**

## What it does

- A branching decision engine walks the player through storm stages (`T-120h` → landfall → recovery), tracking cash, supplies, insurance, and evacuation state.
- An **AI Preparedness Coach** on the final report — Gemini identifies the single decision that hurt most, the one that helped most, and one concrete change, grounded in the player's actual choices (not generic advice). Every consequence still comes from a deterministic rules engine; AI explains the outcome, it doesn't decide it.
- An **AI Transparency panel** ("How AI is used") shows exactly what each AI feature receives and can't affect — no name/email/account info is ever collected or sent to any provider.
- **Try Again** — replaying the simulation compares your new run against your last one (score deltas, financial loss) and a "What changed?" button has Gemini explain which specific decisions moved the outcome.
- Every final report also includes a spoken debrief and a Solana-verifiable completion record — see [Sponsor integrations](#sponsor-integrations) below.
- A **Readiness Assistant** chatbot answers real hurricane-prep questions (insurance, supplies, evacuation timing) using verified FEMA/NOAA facts, not generic LLM guesses.
- An **Auto Insurance Readiness Quiz** (a second tab inside the Readiness Assistant) — 8 scored, scenario-based questions on what comprehensive vs. liability coverage actually pays for in a storm, total-loss valuation, rental reimbursement, and claim documentation, each with a sourced explanation.
- An **evacuation mobility check** on the T-24 evacuation decision — real distance and travel time (via OpenRouteService) from a fixed starting point to the nearest Miami-Dade shelter, with a feasibility flag if rising flood risk threatens a scooter/transit evacuation before landfall.
- Simulation state persists across backend restarts and redeploys — nobody loses progress mid-storm.

## Design rationale

**Why $400?** The Federal Reserve's *Report on the Economic Well-Being of U.S. Households* uses a $400 unexpected expense as its benchmark for financial resilience — roughly a third of American adults couldn't cover one in cash. For a college student or early-career renter, that's a realistic, razor-thin cash cushion: it forces real trade-offs between groceries, fuel, and protecting what you own. Start with $5,000 instead and every choice is easy — board up the windows, rent an SUV, book a hotel out of town, no hesitation. At $400, every dollar spent on sandbags is a dollar you might need to evacuate later.

**Why five days?** It matches how the National Hurricane Center actually forecasts: the 120-hour (5-day) advisory is the point where a storm track goes from "too erratic to act on" to "the countdown starts." The stages mirror the real disaster lifecycle — watch phase (T-120 to T-72, low urgency, normal prices), warning phase (T-48 to T-24, evacuation orders, gas runs dry, prices spike), landfall (structural impact, power loss, surge), and the immediate aftermath (grid down, flooding, insurance claims). It's also just the right length for a demo: two days of choices doesn't feel like enough at stake, thirty days drags — five to seven days is enough tension to feel real in a few minutes of play.

## Sponsor integrations

Each of these is a real, working call to the sponsor's API — not a bolted-on demo. Every integration degrades gracefully (falls back or no-ops) if its API key is missing or the remote call fails, so a sponsor outage never breaks the core simulation.

| Sponsor | What it does | Where |
|---|---|---|
| **DigitalOcean** | Hosts the full stack — FastAPI backend + Next.js frontend on App Platform, auto-deploying on every push to `main` | [`.do/app.yaml`](.do/app.yaml) |
| **MongoDB Atlas** | Persists active simulation state (previously an in-memory dict that lost all progress on every redeploy) | [`backend/app/services/mongo_store.py`](backend/app/services/mongo_store.py) |
| **Tiger Data** | Every decision writes a row to a TimescaleDB hypertable (`simulation_telemetry`), backing the per-run timeline endpoint. A continuous aggregate (`simulation_telemetry_hourly`) pre-computes per-stage decision counts and average scores for real-time rollups, and a compression policy keeps older chunks compact | [`backend/app/services/tiger_service.py`](backend/app/services/tiger_service.py) |
| **Snowflake** | Stores real FEMA/NOAA hurricane-prep facts; Cortex AI (RAG + `AI_COMPLETE`) powers the Readiness Assistant's grounded answers, with a Gemini fallback when Cortex is unavailable | [`backend/app/services/snowflake_service.py`](backend/app/services/snowflake_service.py) |
| **Google Gemini** | Generates the personalized "what you did well / what to improve" plan text on the final report, and backs the Readiness Assistant when Snowflake Cortex can't answer | [`backend/app/services/plan_service.py`](backend/app/services/plan_service.py), [`backend/app/services/assistant_service.py`](backend/app/services/assistant_service.py) |
| **ElevenLabs** | Narrates the final report as spoken audio, and generates the ambient storm sound effect that plays during the simulation | [`backend/app/services/audio_service.py`](backend/app/services/audio_service.py) |
| **Solana** | Records a memo transaction on devnet when a simulation completes (outcome + score), giving players a verifiable, shareable completion record on Solana Explorer | [`backend/app/services/solana_service.py`](backend/app/services/solana_service.py) |

## Tech stack

- **Backend:** FastAPI, Pydantic, pytest — [backend/README.md](backend/README.md)
- **Frontend:** Next.js 16 (App Router), React 19, Tailwind CSS, TypeScript — [frontend/README.md](frontend/README.md)
- **Data:** Tiger Data (Timescale), MongoDB Atlas, Snowflake
- **Deployment:** DigitalOcean App Platform ([`.do/app.yaml`](.do/app.yaml)), auto-deploys on push to `main`, custom domain via Porkbun DNS

## API

Full endpoint reference: [backend/API.md](backend/API.md)

## Running locally

```bash
# backend
cd backend && cp .env.example .env && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && uvicorn app.main:app --reload

# frontend
cd frontend && cp .env.local.example .env.local && npm install && npm run dev
```

All sponsor integrations are optional locally — leave their API keys unset in `.env` and the app runs with in-memory state and no AI/audio/blockchain features. See [backend/README.md](backend/README.md) for details on each variable.

## Testing

```bash
cd backend && pytest -q
```

## Team

[varshith-k](https://github.com/varshith-k) · [sreeramgvp11](https://github.com/sreeramgvp11) · [Harshini1814](https://github.com/Harshini1814) · [Dheeraj2125](https://github.com/Dheeraj2125)
