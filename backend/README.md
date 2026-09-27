# Hurricane Week Backend

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Copy env file from repo root:

```bash
cp ../.env.example .env
```

## Run API

```bash
uvicorn app.main:app --reload
```

## Run tests

```bash
pytest -q
```

## Implemented endpoints

- `GET /api/health`
- `POST /api/simulations`
- `GET /api/simulations/{simulation_id}/event`
- `POST /api/simulations/{simulation_id}/decisions`
- `GET /api/simulations/{simulation_id}/timeline`
- `GET /api/simulations/{simulation_id}/report`
- `GET /api/simulations/{simulation_id}/audio`
- `GET /api/ambient-sound`
- `GET /api/assistant/intro`
- `POST /api/assistant/ask`
- `POST /api/context/refresh`

Full request/response shapes: [API.md](API.md).

## Postgres telemetry

Set `DATABASE_URL` in `.env` to any Postgres connection string (DigitalOcean Managed Postgres in production). Every valid decision writes one telemetry row to `simulation_telemetry`, and `GET /api/simulations/{simulation_id}/timeline` reads those persisted rows back in timestamp order. Optional locally — the app degrades gracefully if unset.

## Optional integrations

MongoDB, Snowflake, Gemini, ElevenLabs, and Solana are all optional locally and degrade gracefully if their env vars are unset. See [.env.example](../.env.example) for every variable, and the top-level [README](../README.md#sponsor-integrations) for what each one does.
