from __future__ import annotations

from sqlalchemy import text

from app.core.database import SessionLocal


def print_rows(name: str, sql: str) -> None:
    print(f"--- {name}")
    db = SessionLocal()
    try:
        rows = db.execute(text(sql)).all()
        if not rows:
            print("(none)")
            return
        for row in rows:
            print(tuple(row))
    finally:
        db.close()


def main() -> None:
    print_rows(
        "drug",
        """
        SELECT TOP 10 ThuocId, TenThuoc
        FROM dbo.Thuoc
        WHERE TenThuoc LIKE N'%Doxid%'
        ORDER BY TenThuoc
        """,
    )
    print_rows(
        "disease",
        """
        SELECT TOP 10 BenhId, TenBenh
        FROM dbo.Benh
        WHERE TenBenh LIKE N'%Abdominal cramp%'
        ORDER BY TenBenh
        """,
    )
    print_rows(
        "link_count_disease",
        """
        SELECT b.BenhId, b.TenBenh, COUNT(lk.LienKetId) AS SoLienKet
        FROM dbo.Benh b
        LEFT JOIN dbo.LienKetThuocBenh lk ON lk.BenhId = b.BenhId
        WHERE b.TenBenh LIKE N'%Abdominal cramp%'
        GROUP BY b.BenhId, b.TenBenh
        """,
    )
    print_rows(
        "top_disease_links",
        """
        SELECT TOP 10 t.ThuocId, t.TenThuoc, lk.DiemLienKet
        FROM dbo.LienKetThuocBenh lk
        JOIN dbo.Thuoc t ON t.ThuocId = lk.ThuocId
        JOIN dbo.Benh b ON b.BenhId = lk.BenhId
        WHERE b.TenBenh LIKE N'%Abdominal cramp%'
        ORDER BY lk.DiemLienKet DESC
        """,
    )
    print_rows(
        "pair",
        """
        SELECT TOP 10 t.ThuocId, t.TenThuoc, b.BenhId, b.TenBenh, lk.DiemLienKet
        FROM dbo.Thuoc t
        CROSS JOIN dbo.Benh b
        LEFT JOIN dbo.LienKetThuocBenh lk ON lk.ThuocId = t.ThuocId AND lk.BenhId = b.BenhId
        WHERE t.TenThuoc LIKE N'%Doxid%' AND b.TenBenh LIKE N'%Abdominal cramp%'
        """,
    )


if __name__ == "__main__":
    main()
