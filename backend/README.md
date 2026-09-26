# Hurricane Week Backend (Sprint 1 + Sprint 2)

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
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

## Tiger Data telemetry

Set `DATABASE_URL` in `.env` to your Tiger Cloud/Timescale Postgres connection string. Every valid decision writes one telemetry row to `simulation_telemetry`, and `GET /api/simulations/{simulation_id}/timeline` reads those persisted rows back in timestamp order.
