import logging
from uuid import UUID

from fastapi import HTTPException

try:
    from psycopg import Error
    from psycopg.rows import dict_row
    from psycopg.types.json import Json
except ModuleNotFoundError:  # pragma: no cover
    Error = Exception  # type: ignore[assignment]
    dict_row = None
    Json = None

from app.core.db import get_database_url, get_db_connection

logger = logging.getLogger(__name__)


class TigerService:
    def __init__(self) -> None:
        self.enabled = bool(get_database_url() and dict_row is not None and Json is not None)
        if self.enabled:
            try:
                self._ensure_telemetry_table()
                self._ensure_analytics()
            except Exception:  # noqa: BLE001 - never let a Tiger Data hiccup block app startup
                logger.exception("Tiger Data setup failed; disabling telemetry")
                self.enabled = False

    def _ensure_telemetry_table(self) -> None:
        ddl = """
            CREATE TABLE IF NOT EXISTS simulation_telemetry (
                simulation_id UUID NOT NULL,
                ts TIMESTAMPTZ NOT NULL DEFAULT now(),
                stage TEXT NOT NULL,
                event_id TEXT NOT NULL,
                choice_id TEXT NOT NULL,
                cash INTEGER NOT NULL,
                preparedness_points INTEGER NOT NULL,
                timing_points INTEGER NOT NULL,
                safety_score INTEGER NOT NULL,
                financial_score INTEGER NOT NULL,
                preparedness_score INTEGER NOT NULL,
                timing_score INTEGER NOT NULL,
                overall_score INTEGER NOT NULL,
                payload JSONB NOT NULL DEFAULT '{}'::jsonb
            );

            CREATE INDEX IF NOT EXISTS simulation_telemetry_simulation_id_ts_idx
            ON simulation_telemetry (simulation_id, ts);
        """

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(ddl)
                connection.commit()
        except Error as exc:
            raise HTTPException(status_code=503, detail=f"Tiger Data schema initialization failed: {exc}") from exc

    def _ensure_analytics(self) -> None:
        """Sets up TimescaleDB-specific features on top of the plain table:
        a continuous aggregate for real-time per-stage rollups, and a
        compression policy for older chunks. Best-effort - the app works
        fine on plain Postgres or if this has already been set up.
        """
        statements = [
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS simulation_telemetry_hourly
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 hour', ts) AS bucket,
                stage,
                count(*) AS decisions,
                avg(overall_score) AS avg_overall_score,
                avg(cash) AS avg_cash
            FROM simulation_telemetry
            GROUP BY bucket, stage
            WITH NO DATA;
            """,
            """
            SELECT add_continuous_aggregate_policy('simulation_telemetry_hourly',
                start_offset => NULL,
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => TRUE);
            """,
            """
            ALTER TABLE simulation_telemetry SET (
                timescaledb.compress,
                timescaledb.compress_segmentby = 'simulation_id',
                timescaledb.compress_orderby = 'ts DESC'
            );
            """,
            "SELECT add_compression_policy('simulation_telemetry', INTERVAL '7 days', if_not_exists => TRUE);",
        ]
        with get_db_connection() as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                for statement in statements:
                    try:
                        cursor.execute(statement)
                    except Error:
                        logger.warning("Tiger Data analytics statement skipped (likely not TimescaleDB, or already set up): %s", statement.strip()[:80])

    def get_hourly_summary(self, limit: int = 24) -> list[dict]:
        if not self.enabled:
            return []
        query = """
            SELECT bucket, stage, decisions, avg_overall_score, avg_cash
            FROM simulation_telemetry_hourly
            ORDER BY bucket DESC
            LIMIT %(limit)s
        """
        try:
            with get_db_connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:  # type: ignore[arg-type]
                    cursor.execute(query, {"limit": limit})
                    rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Error:
            logger.warning("Tiger Data hourly summary query failed")
            return []

    def log_simulation_state(
        self,
        simulation_id: UUID,
        stage: str,
        event_id: str,
        choice_id: str,
        state: dict,
        scores: dict[str, int],
        payload: dict,
    ) -> None:
        if not self.enabled:
            return

        insert_query = """
            INSERT INTO simulation_telemetry (
                simulation_id,
                stage,
                event_id,
                choice_id,
                cash,
                preparedness_points,
                timing_points,
                safety_score,
                financial_score,
                preparedness_score,
                timing_score,
                overall_score,
                payload
            ) VALUES (
                %(simulation_id)s,
                %(stage)s,
                %(event_id)s,
                %(choice_id)s,
                %(cash)s,
                %(preparedness_points)s,
                %(timing_points)s,
                %(safety_score)s,
                %(financial_score)s,
                %(preparedness_score)s,
                %(timing_score)s,
                %(overall_score)s,
                %(payload)s::jsonb
            )
        """

        params = {
            "simulation_id": simulation_id,
            "stage": stage,
            "event_id": event_id,
            "choice_id": choice_id,
            "cash": state["cash"],
            "preparedness_points": state["preparedness_points"],
            "timing_points": state["timing_points"],
            "safety_score": scores["safety"],
            "financial_score": scores["financial"],
            "preparedness_score": scores["preparedness"],
            "timing_score": scores["timing"],
            "overall_score": scores["overall"],
            "payload": Json(payload),
        }

        try:
            with get_db_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(insert_query, params)
                connection.commit()
        except Error:
            # Telemetry is decoration for the timeline/analytics views, never
            # the gameplay itself - a Tiger Data blip must not fail a decision.
            logger.warning("Tiger Data telemetry insert failed; continuing without it")

    def get_simulation_timeline(self, simulation_id: UUID) -> list[dict]:
        if not self.enabled:
            return []

        query = """
            SELECT
                simulation_id,
                ts,
                stage,
                event_id,
                choice_id,
                cash,
                preparedness_points,
                timing_points,
                safety_score,
                financial_score,
                preparedness_score,
                timing_score,
                overall_score,
                payload
            FROM simulation_telemetry
            WHERE simulation_id = %(simulation_id)s
            ORDER BY ts ASC
        """

        try:
            with get_db_connection() as connection:
                with connection.cursor(row_factory=dict_row) as cursor:  # type: ignore[arg-type]
                    cursor.execute(query, {"simulation_id": simulation_id})
                    rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Error as exc:
            raise HTTPException(status_code=503, detail=f"Tiger Data query failed: {exc}") from exc
