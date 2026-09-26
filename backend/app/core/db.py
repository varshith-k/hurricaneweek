import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from dotenv import load_dotenv

try:
    from psycopg import Connection, connect
except ModuleNotFoundError:  # pragma: no cover
    Connection = object  # type: ignore[assignment]
    connect = None


_BACKEND_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_BACKEND_ROOT / ".env", encoding="utf-8-sig")


def get_database_url() -> str | None:
    return os.getenv("DATABASE_URL")


@contextmanager
def get_db_connection() -> Iterator[Connection]:
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    if connect is None:
        raise RuntimeError("psycopg is not installed")

    connection = connect(database_url)
    try:
        yield connection
    finally:
        connection.close()

