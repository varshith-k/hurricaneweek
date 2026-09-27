# Hurricane Week API

Base path: `/api`. All bodies are JSON. The simulator endpoints never depend on
Snowflake; the assistant and context endpoints degrade to cached facts and
verified answers when Snowflake or the LLM is unavailable.

## Simulation

| Method | Path | Notes |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` |
| POST | `/simulations` | Body `{player_profile, seed?}` → `{simulation_id, state}` |
| GET | `/simulations/{id}` | Current `SimulationState` |
| GET | `/simulations/{id}/event` | Current event; choices carry `cost` |
| POST | `/simulations/{id}/decisions` | Body `{event_id, choice_id}` |
| GET | `/simulations/{id}/report` | `FinalReport` (409 until complete) |
| GET | `/simulations/{id}/audio` | Spoken debrief MP3 (404 if unavailable) |
| GET | `/simulations/{id}/timeline` | Persisted telemetry rows |

`FinalReport.real_world_context` is a list of `Fact` objects (see below) from
the cached Snowflake facts; it is `[]` when no facts are cached.

## Readiness Assistant

### `GET /assistant/intro?simulation_id=<uuid>`

`simulation_id` is optional; pass it when a run exists.

```json
{
  "emergency_notice": "If you or someone else is in danger right now, call 911. ...",
  "powered_by": {
    "snowflake_configured": true,
    "cortex_model": "llama3.1-70b",
    "embed_model": "snowflake-arctic-embed-m-v1.5",
    "rag_enabled": true,
    "vector_search": true,
    "facts_count": 4,
    "data_credit": "Snowflake Public Data · FEMA & NOAA",
    "gemini_backup": false
  },
  "location_label": "Miami-Dade County, Florida",
  "area_notes": ["..."],
  "facts": [Fact],
  "facts_updated_at": "2026-09-26T20:15:00+00:00",
  "facts_source": "snowflake-live | cache | none",
  "last_run": LastRun | null,
  "suggested_questions": [{"id": "renters_insurance_flood", "question": "Does renters insurance cover flooding?"}]
}
```

`cortex_model` is null when Cortex is not in use; `embed_model` is null unless
RAG (vector search) is on.

`Fact`:

```json
{"id": "irma_nfip_claims_miami_dade", "label": "...", "value_num": 1234, "unit": "claims", "source": "...", "note": "exact filters used"}
```

`LastRun`:

```json
{"simulation_id": "uuid", "status": "active | completed", "stage": "LANDFALL", "outcome": "Well Prepared | null",
 "overall_score": 82, "preparedness_gaps": ["..."], "action_identifiers": ["..."]}
```

`outcome`, `preparedness_gaps`, and `action_identifiers` are filled only for
completed runs. Suggested questions are personalized from `action_identifiers`.

### `POST /assistant/ask`

Body: exactly one of `question` (free text, ≤ 500 chars) or `question_id`
(from `suggested_questions`), plus optional `simulation_id` and `history`
(the last 4 turns, kept only in the browser):

```json
{"question": "Does renters insurance cover flooding?", "simulation_id": "uuid",
 "history": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

Response:

```json
{
  "kind": "emergency | verified | ai | fallback",
  "answer": "text",
  "question_id": "id or null",
  "sources": ["..."],
  "note": "why a fallback was used, or null",
  "ai_meta": {
    "provider": "snowflake-cortex-rag | snowflake-cortex | gemini",
    "model": "llama3.1-70b",
    "embed_model": "snowflake-arctic-embed-m-v1.5 or null",
    "retrieved": [{"id": "kb:renters_insurance_flood", "source": "...", "score": 0.83}],
    "latency_ms": 1840,
    "sql_statement": "statements with <question>/<prompt> placeholders, or null",
    "number_check": "passed | failed"
  }
}
```

How `kind` is decided:

1. **emergency**: the question signals immediate danger. Fixed guidance is
   returned, no LLM is called, and `ai_meta` is null.
2. **verified**: a `question_id` was sent, or the AI was unavailable or failed
   the number check and a verified answer matched. `ai_meta` is present only
   when an AI answer was attempted.
3. **ai**: an LLM answered and every number in the answer appeared in the
   retrieved context (`number_check: "passed"`).
4. **fallback**: nothing reliable was available; a safe pointer to official
   sources.

Badges for the UI: emergency → red alert card; verified → "Verified answer";
ai + `snowflake-cortex-rag` → "Snowflake Cortex · RAG"; ai + `snowflake-cortex`
→ "Snowflake Cortex"; ai + `gemini` → "Gemini (backup)"; add "✓ Number-checked"
when `number_check` is `passed`. Show `sources` under every answer.

### `POST /context/refresh`

Re-reads `FACTS` from Snowflake and updates the offline cache
(`app/data/snowflake_facts.json`).

```json
{"source": "snowflake-live | cache | none", "facts_count": 4, "facts": [Fact],
 "updated_at": "2026-09-26T20:15:00+00:00", "error": "message or null"}
```

On failure it returns 200 with the cached facts and an `error` message.

## Configuration (backend/.env)

| Key | Purpose |
|---|---|
| `SNOWFLAKE_ACCOUNT` | Account identifier, e.g. `orgname-accountname` |
| `SNOWFLAKE_PAT` | Programmatic access token for the `HW_APP` role (secret) |
| `SNOWFLAKE_ROLE` / `SNOWFLAKE_WAREHOUSE` | Default `HW_APP` / `HW_WH` |
| `SNOWFLAKE_FACTS_TABLE` / `SNOWFLAKE_KNOWLEDGE_TABLE` | Fully qualified table names |
| `SNOWFLAKE_CORTEX_MODEL` / `SNOWFLAKE_EMBED_MODEL` | Models verified in setup |
| `SNOWFLAKE_RAG` | `on` to use vector search over `KNOWLEDGE` |
| `ASSISTANT_LLM` | `cortex` (default), `gemini`, or `none` |
| `GEMINI_API_KEY` / `GEMINI_MODEL` | Optional backup LLM |
