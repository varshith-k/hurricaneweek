# Hurricane Week

An interactive hurricane-preparedness simulator. You play a Miami-Dade resident with $400 and five days before landfall — every decision (evacuate or shelter, insure or risk it, spend or save) changes your safety, finances, and outcome score. Built for ShellHacks/MLH 2026.

**Live: [hurricaneweek.miami](https://hurricaneweek.miami)**

## What it does

- A branching decision engine walks the player through storm stages (`T-120h` → landfall → recovery), tracking cash, supplies, insurance, and evacuation state.
- Every final report includes a personalized action plan, a spoken debrief, and a Solana-verifiable completion record — see [Sponsor integrations](#sponsor-integrations) below.
- A **Readiness Assistant** chatbot answers real hurricane-prep questions (insurance, supplies, evacuation timing) using verified FEMA/NOAA facts, not generic LLM guesses.
- Simulation state persists across backend restarts and redeploys — nobody loses progress mid-storm.

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
