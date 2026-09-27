"""Snowflake SQL REST API client, real-world facts cache, and Cortex RAG calls.

Everything here is optional: when Snowflake is not configured or unreachable,
callers fall back to the cached facts file and verified content. The game
simulation never calls into this module.
"""

import json
import logging
import os
import re
import time
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any

import httpx
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parents[2]
FACTS_CACHE_PATH = _BACKEND_ROOT / "app" / "data" / "snowflake_facts.json"

# Table names cannot be bound as SQL parameters, so only plain identifiers are accepted.
_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*(\.[A-Za-z_][A-Za-z0-9_$]*){0,2}$")

RETRIEVAL_SQL = (
    "SELECT ID, CHUNK, SOURCE, "
    "VECTOR_COSINE_SIMILARITY(EMBEDDING, SNOWFLAKE.CORTEX.EMBED_TEXT_768(?, ?)) AS SCORE "
    "FROM {table} ORDER BY SCORE DESC LIMIT ?"
)
COMPLETE_SQL = "SELECT AI_COMPLETE(?, ?) AS ANSWER"
FACTS_SQL = "SELECT ID, LABEL, VALUE_NUM, UNIT, SOURCE, NOTE, UPDATED_AT FROM {table} ORDER BY ID"


class SnowflakeError(Exception):
    """Any failure talking to Snowflake: config, network, auth, or SQL."""


@dataclass(frozen=True)
class SnowflakeConfig:
    account: str
    token: str
    role: str
    warehouse: str
    facts_table: str
    knowledge_table: str
    cortex_model: str
    embed_model: str
    rag_enabled: bool

    @classmethod
    def from_env(cls) -> "SnowflakeConfig":
        load_dotenv(_BACKEND_ROOT / ".env", encoding="utf-8-sig")
        env = lambda key, default="": os.getenv(key, default).strip()  # noqa: E731
        return cls(
            account=env("SNOWFLAKE_ACCOUNT"),
            token=env("SNOWFLAKE_PAT"),
            role=env("SNOWFLAKE_ROLE", "HW_APP"),
            warehouse=env("SNOWFLAKE_WAREHOUSE", "HW_WH"),
            facts_table=env("SNOWFLAKE_FACTS_TABLE", "HURRICANE_WEEK.APP.FACTS"),
            knowledge_table=env("SNOWFLAKE_KNOWLEDGE_TABLE", "HURRICANE_WEEK.APP.KNOWLEDGE"),
            cortex_model=env("SNOWFLAKE_CORTEX_MODEL", "llama3.1-70b"),
            embed_model=env("SNOWFLAKE_EMBED_MODEL", "snowflake-arctic-embed-m-v1.5"),
            rag_enabled=env("SNOWFLAKE_RAG", "off").lower() == "on",
        )

    @property
    def configured(self) -> bool:
        return bool(self.account and self.token)


def account_host(account: str) -> str:
    """Account identifiers use '_' in names but '-' in hostnames."""
    return f"https://{account.strip().lower().replace('_', '-')}.snowflakecomputing.com"


def checked_identifier(name: str) -> str:
    if not _IDENTIFIER.match(name):
        raise SnowflakeError(f"Invalid table name: {name!r}")
    return name


def _binding(value: Any) -> dict[str, str]:
    if isinstance(value, bool):
        return {"type": "BOOLEAN", "value": str(value).lower()}
    if isinstance(value, int):
        return {"type": "FIXED", "value": str(value)}
    if isinstance(value, float):
        return {"type": "REAL", "value": repr(value)}
    return {"type": "TEXT", "value": str(value)}


def convert_value(value: str | None, column_type: str) -> Any:
    if value is None:
        return None
    if column_type == "fixed":
        number = float(value)
        return int(number) if number.is_integer() else number
    if column_type == "real":
        return float(value)
    if column_type == "boolean":
        return value.lower() == "true"
    if column_type == "date":
        # The SQL API encodes DATE as days since the Unix epoch.
        return (date(1970, 1, 1) + timedelta(days=int(value))).isoformat()
    if column_type in {"timestamp_ntz", "timestamp_ltz", "timestamp_tz"}:
        # Seconds since the epoch, optionally followed by a time zone offset in minutes.
        seconds = float(value.split()[0])
        return datetime.fromtimestamp(seconds, UTC).replace(tzinfo=None).isoformat(timespec="seconds")
    return value


class SnowflakeClient:
    """Minimal client for POST /api/v2/statements using a programmatic access token."""

    def __init__(
        self,
        account: str,
        token: str,
        role: str | None = None,
        warehouse: str | None = None,
        timeout: float = 45.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not account or not token:
            raise SnowflakeError("Snowflake account or token is not configured")
        self.base_url = account_host(account)
        self.role = role
        self.warehouse = warehouse
        self.timeout = timeout
        self._http = httpx.Client(
            base_url=self.base_url,
            timeout=timeout,
            transport=transport,
            headers={
                "Authorization": f"Bearer {token}",
                "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "hurricane-week/1.0",
            },
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "SnowflakeClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _error(response: httpx.Response) -> SnowflakeError:
        try:
            payload = response.json()
            message = payload.get("message") or response.text
            code = payload.get("code")
        except ValueError:
            message, code = response.text, None
        prefix = f"Snowflake {response.status_code}" + (f" ({code})" if code else "")
        return SnowflakeError(f"{prefix}: {message}".strip())

    def execute_raw(self, statement: str, bindings: list[Any] | None = None) -> dict:
        body: dict[str, Any] = {"statement": statement, "timeout": int(self.timeout)}
        if self.role:
            body["role"] = self.role
        if self.warehouse:
            body["warehouse"] = self.warehouse
        if bindings:
            body["bindings"] = {str(index): _binding(value) for index, value in enumerate(bindings, start=1)}

        try:
            response = self._http.post("/api/v2/statements", json=body)
            deadline = time.monotonic() + self.timeout
            while response.status_code == 202:
                if time.monotonic() > deadline:
                    raise SnowflakeError("Snowflake statement timed out")
                handle = response.json()["statementHandle"]
                time.sleep(0.5)
                response = self._http.get(f"/api/v2/statements/{handle}")
            if response.status_code != 200:
                raise self._error(response)

            result = response.json()
            partitions = result.get("resultSetMetaData", {}).get("partitionInfo", [])
            handle = result.get("statementHandle")
            for partition in range(1, len(partitions)):
                extra = self._http.get(f"/api/v2/statements/{handle}", params={"partition": partition})
                if extra.status_code != 200:
                    raise self._error(extra)
                result["data"].extend(extra.json().get("data", []))
            return result
        except httpx.HTTPError as exc:
            raise SnowflakeError(f"Snowflake request failed: {type(exc).__name__}") from exc

    def execute(self, statement: str, bindings: list[Any] | None = None) -> list[dict[str, Any]]:
        """Runs one statement and returns rows as dicts keyed by upper-case column name."""
        result = self.execute_raw(statement, bindings)
        columns = result.get("resultSetMetaData", {}).get("rowType", [])
        names = [column["name"].upper() for column in columns]
        types = [column.get("type", "text").lower() for column in columns]
        return [
            {name: convert_value(value, column_type) for name, value, column_type in zip(names, row, types)}
            for row in result.get("data", [])
        ]


def client_from_config(config: SnowflakeConfig, timeout: float = 45.0) -> SnowflakeClient:
    return SnowflakeClient(config.account, config.token, role=config.role, warehouse=config.warehouse, timeout=timeout)


class FactsRepository:
    """Real-world facts from Snowflake, cached on disk so they work offline."""

    def __init__(self, cache_path: Path = FACTS_CACHE_PATH) -> None:
        self.cache_path = cache_path
        self._lock = Lock()

    def load(self) -> dict[str, Any]:
        try:
            payload = json.loads(self.cache_path.read_text(encoding="utf-8"))
            return {"facts": payload.get("facts", []), "updated_at": payload.get("updated_at"), "source": "cache"}
        except (OSError, ValueError):
            return {"facts": [], "updated_at": None, "source": "none"}

    def refresh(self, client: SnowflakeClient, facts_table: str) -> dict[str, Any]:
        rows = client.execute(FACTS_SQL.format(table=checked_identifier(facts_table)))
        facts = [
            {
                "id": row["ID"],
                "label": row["LABEL"],
                "value_num": row["VALUE_NUM"],
                "unit": row["UNIT"],
                "source": row["SOURCE"],
                "note": row["NOTE"],
            }
            for row in rows
        ]
        updated_at = datetime.now(UTC).isoformat(timespec="seconds")
        payload = {"facts": facts, "updated_at": updated_at}
        with self._lock:
            temporary = self.cache_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            temporary.replace(self.cache_path)
        return {"facts": facts, "updated_at": updated_at, "source": "snowflake-live"}


def retrieve_chunks(client: SnowflakeClient, config: SnowflakeConfig, question: str, limit: int = 4) -> list[dict[str, Any]]:
    sql = RETRIEVAL_SQL.format(table=checked_identifier(config.knowledge_table))
    rows = client.execute(sql, [config.embed_model, question, limit])
    return [
        {"id": row["ID"], "chunk": row["CHUNK"], "source": row["SOURCE"], "score": round(float(row["SCORE"]), 4)}
        for row in rows
    ]


def complete(client: SnowflakeClient, model: str, prompt: str) -> str:
    rows = client.execute(COMPLETE_SQL, [model, prompt])
    answer = rows[0]["ANSWER"] if rows else ""
    # AI_COMPLETE can return a JSON-encoded string; unwrap it when it does.
    if isinstance(answer, str) and answer.startswith('"') and answer.endswith('"'):
        try:
            answer = json.loads(answer)
        except ValueError:
            pass
    return (answer or "").strip()


def display_sql(config: SnowflakeConfig) -> str:
    """The statements the assistant runs, with user data replaced by placeholders."""
    table = config.knowledge_table
    return (
        "-- 1) Embed the question and find the closest knowledge chunks\n"
        "SELECT ID, CHUNK, SOURCE,\n"
        f"       VECTOR_COSINE_SIMILARITY(EMBEDDING, SNOWFLAKE.CORTEX.EMBED_TEXT_768('{config.embed_model}', '<question>')) AS SCORE\n"
        f"FROM {table}\nORDER BY SCORE DESC\nLIMIT 4;\n\n"
        "-- 2) Write the answer from those chunks only\n"
        f"SELECT AI_COMPLETE('{config.cortex_model}', '<instructions + retrieved chunks + question>') AS ANSWER;"
    )
