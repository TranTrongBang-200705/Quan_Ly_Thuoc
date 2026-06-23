from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SQL = ROOT / "database" / "DataThuoc_Final_Clean_Codex.sql"
OUTPUT_SQL = ROOT / "database" / "postgres_seed.sql"

IDENTITY_COLUMNS = {
    "NguonDuLieu": "NguonDuLieuId",
    "TrangThaiKiemDuyet": "TrangThaiKiemDuyetId",
    "MucTinCay": "MucTinCayId",
    "NhomThuoc": "NhomThuocId",
    "NhomBenh": "NhomBenhId",
    "LoaiLienKet": "LoaiLienKetId",
    "VaiTro": "VaiTroId",
    "Thuoc": "ThuocId",
    "Benh": "BenhId",
    "LienKetThuocBenh": "LienKetId",
    "TapDuLieuHuanLuyen": "TapDuLieuId",
    "MoHinhMayHoc": "MoHinhId",
}

INSERT_RE = re.compile(r"^INSERT INTO dbo\.([A-Za-z0-9_]+) \((.+)\)")


def quote_identifier(value: str) -> str:
    return '"' + value.strip().replace('"', '""') + '"'


def convert_insert(line: str) -> str | None:
    match = INSERT_RE.match(line)
    if not match:
        return None
    table, raw_columns = match.groups()
    columns = ", ".join(quote_identifier(column) for column in raw_columns.split(","))
    return f"INSERT INTO {quote_identifier(table)} ({columns})"


def convert_line(line: str) -> str | None:
    stripped = line.strip()
    if not stripped:
        return ""
    if stripped.upper() == "GO":
        return None
    if stripped.upper().startswith(("USE ", "SET NOCOUNT", "SET XACT_ABORT", "SET IDENTITY_INSERT", "BEGIN TRANSACTION", "COMMIT TRANSACTION")):
        return None
    if stripped.upper().startswith(("SELECT ", "DECLARE ")):
        return None
    if stripped.startswith("--"):
        return line

    converted = convert_insert(stripped)
    if converted:
        return converted

    line = line.replace("@TapDuLieuId", '(SELECT MAX("TapDuLieuId") FROM "TapDuLieuHuanLuyen")')
    line = re.sub(r"\bN'", "'", line)
    line = line.replace("dbo.", "")
    if "MH_THAM_CHIEU_001" in line:
        line = line.replace(", 0,", ", false,")
    return line


def sequence_resets() -> list[str]:
    lines = ["", "-- Reset PostgreSQL sequences after explicit identity inserts."]
    for table, column in IDENTITY_COLUMNS.items():
        lines.append(
            "SELECT setval("
            f"pg_get_serial_sequence('{quote_identifier(table)}', '{column}'), "
            f"COALESCE((SELECT MAX({quote_identifier(column)}) FROM {quote_identifier(table)}), 1), true"
            ");"
        )
    return lines


def main() -> None:
    if not SOURCE_SQL.exists():
        raise SystemExit(f"Source SQL not found: {SOURCE_SQL}")

    output: list[str] = [
        "-- Generated from database/DataThuoc_Final_Clean_Codex.sql.",
        "-- Run this after creating tables with SQLAlchemy metadata/create_all.",
        "BEGIN;",
    ]
    in_insert = False
    for raw_line in SOURCE_SQL.read_text(encoding="utf-8-sig").splitlines():
        stripped = raw_line.strip()
        if stripped.startswith("INSERT INTO dbo."):
            in_insert = True
            converted = convert_line(raw_line)
        elif in_insert:
            converted = convert_line(raw_line)
        else:
            converted = None

        if converted is not None and converted != "":
            output.append(converted)
        if in_insert and stripped.endswith(";"):
            in_insert = False
        if "COMMIT TRANSACTION" in raw_line:
            break

    output.extend(sequence_resets())
    output.append("COMMIT;")
    OUTPUT_SQL.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT_SQL}")


if __name__ == "__main__":
    main()
