"""Run SQL against Snowflake through the SQL REST API (the only way this project runs setup SQL).

Examples (from backend/):
  .venv/bin/python snowflake/run_sql.py --token setup --sql "SELECT CURRENT_USER()"
  .venv/bin/python snowflake/run_sql.py --token setup --file snowflake/setup_final.sql
  .venv/bin/python snowflake/run_sql.py --token app --role HW_APP --sql "SELECT COUNT(*) FROM HURRICANE_WEEK.APP.KNOWLEDGE"
  .venv/bin/python snowflake/run_sql.py --token setup --capture-token SNOWFLAKE_PAT --sql "ALTER USER ... ADD PROGRAMMATIC ACCESS TOKEN ..."

Secrets are read from backend/.env and never printed. Each statement is sent as
its own request; USE ROLE / USE WAREHOUSE statements are applied to the
statements that follow.
"""

import argparse
import json
import re
import sys
from pathlib import Path

from dotenv import dotenv_values

BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_ROOT / ".env"
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.snowflake_service import SnowflakeClient, SnowflakeError, convert_value  # noqa: E402

TOKEN_KEYS = {"setup": "SNOWFLAKE_SETUP_PAT", "app": "SNOWFLAKE_PAT"}
DEFAULT_ROLES = {"setup": "ACCOUNTADMIN", "app": "HW_APP"}
MAX_ROWS = 25
MAX_CELL = 60


def split_statements(sql: str) -> list[str]:
    """Split on semicolons outside quotes, identifiers, comments, and $$ blocks."""
    statements, current = [], []
    i, n = 0, len(sql)
    while i < n:
        char = sql[i]
        if char == "-" and sql.startswith("--", i):
            end = sql.find("\n", i)
            end = n if end == -1 else end
            current.append(sql[i:end])
            i = end
        elif char == "/" and sql.startswith("/*", i):
            end = sql.find("*/", i + 2)
            end = n if end == -1 else end + 2
            current.append(sql[i:end])
            i = end
        elif char == "$" and sql.startswith("$$", i):
            end = sql.find("$$", i + 2)
            end = n if end == -1 else end + 2
            current.append(sql[i:end])
            i = end
        elif char in ("'", '"'):
            j = i + 1
            while j < n:
                if sql[j] == "\\" and char == "'":
                    j += 2
                    continue
                if sql[j] == char:
                    if j + 1 < n and sql[j + 1] == char:  # doubled quote escape
                        j += 2
                        continue
                    break
                j += 1
            current.append(sql[i : j + 1])
            i = j + 1
        elif char == ";":
            statements.append("".join(current))
            current = []
            i += 1
        else:
            current.append(char)
            i += 1
    statements.append("".join(current))
    return [statement.strip() for statement in statements if _has_code(statement)]


def _strip_comments(statement: str) -> str:
    without_block = re.sub(r"/\*.*?\*/", " ", statement, flags=re.S)
    return "\n".join(line for line in without_block.splitlines() if not line.strip().startswith("--"))


def _has_code(statement: str) -> bool:
    return bool(_strip_comments(statement).strip())


def first_line(statement: str) -> str:
    for line in _strip_comments(statement).splitlines():
        if line.strip():
            return line.strip()[:120]
    return ""


def print_table(result: dict) -> None:
    row_type = result.get("resultSetMetaData", {}).get("rowType", [])
    columns = [column["name"] for column in row_type]
    types = [column.get("type", "text").lower() for column in row_type]
    rows = result.get("data", [])
    if not columns:
        print("  (no result set)")
        return

    def cell(value, column_type):
        if value is None:
            return "NULL"
        if column_type in {"date", "timestamp_ntz", "timestamp_ltz", "timestamp_tz"}:
            value = convert_value(value, column_type)
        return str(value).replace("\n", " ")[:MAX_CELL]

    shown = [[cell(value, column_type) for value, column_type in zip(row, types)] for row in rows[:MAX_ROWS]]
    widths = [max([len(column)] + [len(row[index]) for row in shown]) for index, column in enumerate(columns)]
    print("  " + " | ".join(column.ljust(width) for column, width in zip(columns, widths)))
    print("  " + "-+-".join("-" * width for width in widths))
    for row in shown:
        print("  " + " | ".join(value.ljust(width) for value, width in zip(row, widths)))
    extra = len(rows) - len(shown)
    print(f"  ({len(rows)} row{'s' if len(rows) != 1 else ''}" + (f", {extra} not shown" if extra > 0 else "") + ")")


def print_json(result: dict) -> None:
    row_type = result.get("resultSetMetaData", {}).get("rowType", [])
    names = [column["name"] for column in row_type]
    types = [column.get("type", "text").lower() for column in row_type]
    for row in result.get("data", [])[:MAX_ROWS]:
        print("  " + json.dumps({name: convert_value(value, kind) for name, value, kind in zip(names, row, types)}, ensure_ascii=False))


def save_env_value(key: str, value: str) -> None:
    text = ENV_PATH.read_text(encoding="utf-8") if ENV_PATH.exists() else ""
    line = f"{key}={value}"
    if re.search(rf"^{re.escape(key)}=.*$", text, flags=re.M):
        text = re.sub(rf"^{re.escape(key)}=.*$", lambda _: line, text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + f"\n{line}\n"
    ENV_PATH.write_text(text, encoding="utf-8")


def capture_token(result: dict, env_key: str) -> bool:
    columns = [column["name"].lower() for column in result.get("resultSetMetaData", {}).get("rowType", [])]
    if "token_secret" not in columns or not result.get("data"):
        return False
    secret = result["data"][0][columns.index("token_secret")]
    if not secret:
        return False
    save_env_value(env_key, secret)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--sql", help="one SQL statement")
    source.add_argument("--file", type=Path, help="path to a .sql file")
    parser.add_argument("--token", choices=sorted(TOKEN_KEYS), required=True)
    parser.add_argument("--role", help="role for the session (default: ACCOUNTADMIN for setup, HW_APP for app)")
    parser.add_argument("--warehouse", help="warehouse for the session")
    parser.add_argument("--capture-token", metavar="ENV_KEY", help="save token_secret from the result into backend/.env")
    parser.add_argument("--continue-on-error", action="store_true", help="keep going after a failed statement")
    parser.add_argument("--json", action="store_true", help="print full rows as JSON instead of a truncated table")
    args = parser.parse_args()

    env = dotenv_values(ENV_PATH, encoding="utf-8-sig")
    account = (env.get("SNOWFLAKE_ACCOUNT") or "").strip()
    token_key = TOKEN_KEYS[args.token]
    token = (env.get(token_key) or "").strip()
    if not account or not token:
        print(f"SNOWFLAKE_ACCOUNT is {'[set]' if account else '[missing]'}, {token_key} is {'[set]' if token else '[missing]'}")
        return 2

    sql = args.sql if args.sql is not None else args.file.read_text(encoding="utf-8")
    statements = split_statements(sql)
    if args.capture_token and len(statements) != 1:
        print("--capture-token needs exactly one statement")
        return 2

    role = args.role or DEFAULT_ROLES[args.token]
    warehouse = args.warehouse or (env.get("SNOWFLAKE_WAREHOUSE") or "").strip() or None
    failures = 0
    for number, statement in enumerate(statements, start=1):
        print(f"\n[{number}/{len(statements)}] {first_line(statement)}")
        use = re.match(r"^\s*USE\s+(ROLE|WAREHOUSE)\s+(\"[^\"]+\"|[\w$]+)\s*$", _strip_comments(statement), flags=re.I)
        if use:
            # The SQL API has no session between requests, so apply USE locally.
            kind, name = use.group(1).upper(), use.group(2)
            if kind == "ROLE":
                role = name
            else:
                warehouse = name
            print(f"  (session {kind.lower()} set to {name} for the following statements)")
            continue
        try:
            with SnowflakeClient(account, token, role=role, warehouse=warehouse, timeout=120) as client:
                result = client.execute_raw(statement)
        except SnowflakeError as exc:
            failures += 1
            print(f"  ERROR: {exc}")
            if not args.continue_on_error:
                break
            continue
        if args.capture_token:
            if capture_token(result, args.capture_token):
                print(f"  {args.capture_token} saved (hidden)")
            else:
                failures += 1
                print("  ERROR: no token_secret in the result; nothing saved")
            continue
        if args.json:
            print_json(result)
        else:
            print_table(result)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
