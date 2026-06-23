from __future__ import annotations

import os
from pathlib import Path

import psycopg


ROOT = Path(__file__).resolve().parents[1]
SEED_SQL = ROOT / "database" / "postgres_seed.sql"


def normalize_url(url: str) -> str:
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


def main() -> None:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise SystemExit("Set DATABASE_URL before running this script.")
    if not SEED_SQL.exists():
        raise SystemExit(f"Seed file not found: {SEED_SQL}. Run scripts/create_postgres_seed.py first.")

    sql = SEED_SQL.read_text(encoding="utf-8")
    with psycopg.connect(normalize_url(database_url)) as connection:
        with connection.cursor() as cursor:
            cursor.execute(sql)
        connection.commit()
    print("PostgreSQL seed imported.")


if __name__ == "__main__":
    main()
