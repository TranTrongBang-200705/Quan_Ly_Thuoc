from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend" / "DrugDisease.FastApi"))

from app.core.database import Base, engine
import app.models.db_models  # noqa: F401
from sqlalchemy import text


POSTGRES_DEFAULTS = {
    "NguoiDung": ["NgayTao"],
    "NguoiDungVaiTro": ["NgayGan"],
    "NguoiDungPhienDangNhap": ["NgayBatDau"],
    "Thuoc": ["NgayTao"],
    "Benh": ["NgayTao"],
    "LienKetThuocBenh": ["NgayTao"],
    "YeuCauDuDoan": ["NgayTao"],
    "KetQuaDuDoan": ["NgayTao"],
    "PhanHoiKetQua": ["NgayTao"],
    "TapDuLieuHuanLuyen": ["NgayTao"],
}


def apply_postgres_defaults() -> None:
    if engine.dialect.name != "postgresql":
        return
    with engine.begin() as connection:
        for table, columns in POSTGRES_DEFAULTS.items():
            for column in columns:
                connection.execute(
                    text(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" SET DEFAULT CURRENT_TIMESTAMP')
                )


def main() -> None:
    Base.metadata.create_all(bind=engine)
    apply_postgres_defaults()
    print("Database tables created or already exist.")


if __name__ == "__main__":
    main()
