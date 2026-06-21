from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

load_dotenv(ROOT_DIR / ".env", override=False)

from app.core.config import get_settings  # noqa: E402


def main() -> int:
    settings = get_settings()
    last_error: Exception | None = None

    for server, database_url in settings.sqlalchemy_database_urls:
        print(f"Thu ket noi SQL Server: {server}")
        engine = create_engine(database_url, pool_pre_ping=True, future=True)

        try:
            with engine.connect() as connection:
                count = connection.execute(text("SELECT COUNT(*) FROM dbo.NguoiDung")).scalar_one()

            print("Ket noi database thanh cong.")
            print(f"SoNguoiDung: {count}")
            return 0
        except SQLAlchemyError as exc:
            last_error = exc
            print(f"Ket noi that bai voi server '{server}'.")
            print(str(exc).splitlines()[0])
        finally:
            engine.dispose()

    print("Khong ket noi duoc database.")

    if last_error is not None:
        print("Loi cuoi cung:")
        print(last_error)

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
