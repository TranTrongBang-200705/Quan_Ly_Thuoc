from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
import re
import unicodedata
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


CAU_LENH_LAY_DU_LIEU = r"""
SET NOCOUNT ON;

DECLARE @MaxBenhId int = (
    SELECT MAX(BenhId)
    FROM dbo.Benh
);

WITH MauDuong AS
(
    SELECT
        lk.LienKetId AS DatasetItemId,
        lk.ThuocId AS DrugId,
        lk.BenhId AS DiseaseId,
        CAST(1 AS int) AS LabelValue,
        N'ALL' AS SplitName,
        N'{}' AS FeatureVectorJson,
        COALESCE(t.MaThuoc, N'') AS DrugCode,
        COALESCE(t.TenThuoc, N'') AS ActiveName,
        COALESCE(t.TenThuocGoc, N'') AS TradeName,
        COALESCE(CAST(t.NhomThuocId AS nvarchar(30)), N'') AS DrugGroupId,
        N'' AS RouteId,
        COALESCE(CAST(b.NhomBenhId AS nvarchar(30)), N'') AS DiseaseGroupId,
        COALESCE(b.MaBenh, N'') AS DiseaseCode,
        COALESCE(b.TenBenh, N'') AS DiseaseName,
        COALESCE(llt.MaLoaiLienKet, N'UNKNOWN') AS LinkTypeCode,
        COALESCE(mtc.MaMucTinCay, N'UNKNOWN') AS ConfidenceLevelCode,
        COALESCE(CAST(lk.DiemLienKet AS nvarchar(30)), N'') AS SourceScore,
        COALESCE(t.HoatChat, N'') AS HoatChat,
        COALESCE(t.CongDung, N'') AS CongDung,
        COALESCE(t.TacDungPhu, N'') AS TacDungPhu,
        COALESCE(b.MoTa, N'') AS MoTaBenh,
        COALESCE(b.TrieuChung, N'') AS TrieuChung,
        COALESCE(b.ThuocDieuTriDaBiet, N'') AS ThuocDieuTriDaBiet
    FROM dbo.LienKetThuocBenh lk
    JOIN dbo.Thuoc t ON t.ThuocId = lk.ThuocId
    JOIN dbo.Benh b ON b.BenhId = lk.BenhId
    LEFT JOIN dbo.LoaiLienKet llt ON llt.LoaiLienKetId = lk.LoaiLienKetId
    LEFT JOIN dbo.MucTinCay mtc ON mtc.MucTinCayId = lk.MucTinCayId
),
MauAm AS
(
    SELECT
        lkNguon.LienKetId + 100000000 AS DatasetItemId,
        t.ThuocId AS DrugId,
        b.BenhId AS DiseaseId,
        CAST(0 AS int) AS LabelValue,
        N'ALL' AS SplitName,
        N'{}' AS FeatureVectorJson,
        COALESCE(t.MaThuoc, N'') AS DrugCode,
        COALESCE(t.TenThuoc, N'') AS ActiveName,
        COALESCE(t.TenThuocGoc, N'') AS TradeName,
        COALESCE(CAST(t.NhomThuocId AS nvarchar(30)), N'') AS DrugGroupId,
        N'' AS RouteId,
        COALESCE(CAST(b.NhomBenhId AS nvarchar(30)), N'') AS DiseaseGroupId,
        COALESCE(b.MaBenh, N'') AS DiseaseCode,
        COALESCE(b.TenBenh, N'') AS DiseaseName,
        N'UNKNOWN' AS LinkTypeCode,
        N'UNKNOWN' AS ConfidenceLevelCode,
        N'' AS SourceScore,
        COALESCE(t.HoatChat, N'') AS HoatChat,
        COALESCE(t.CongDung, N'') AS CongDung,
        COALESCE(t.TacDungPhu, N'') AS TacDungPhu,
        COALESCE(b.MoTa, N'') AS MoTaBenh,
        COALESCE(b.TrieuChung, N'') AS TrieuChung,
        COALESCE(b.ThuocDieuTriDaBiet, N'') AS ThuocDieuTriDaBiet
    FROM dbo.LienKetThuocBenh lkNguon
    JOIN dbo.Thuoc t ON t.ThuocId = lkNguon.ThuocId
    JOIN dbo.Benh b
        ON b.BenhId =
            CASE
                WHEN lkNguon.BenhId < @MaxBenhId
                THEN lkNguon.BenhId + 1
                ELSE 1
            END
    WHERE NOT EXISTS
    (
        SELECT 1
        FROM dbo.LienKetThuocBenh lk
        WHERE lk.ThuocId = lkNguon.ThuocId
          AND lk.BenhId = b.BenhId
    )
)
SELECT *
FROM MauDuong
UNION ALL
SELECT *
FROM MauAm
ORDER BY DatasetItemId;
"""


def doc_cau_hinh(duong_dan: str | Path) -> dict[str, Any]:
    with Path(duong_dan).open("r", encoding="utf-8") as tep:
        return json.load(tep)


def chay_lenh_sqlcmd(cau_hinh: dict[str, Any]) -> str:
    """Chạy sqlcmd và ép output UTF-8 để không hỏng tiếng Việt."""
    ky_tu_phan_tach = str(cau_hinh.get("ky_tu_phan_tach", "|"))
    tep_sql_tam = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sql",
        delete=False,
        encoding="utf-8",
    )

    try:
        tep_sql_tam.write(CAU_LENH_LAY_DU_LIEU)
        tep_sql_tam.close()

        lenh = [
            "sqlcmd",
            "-S",
            str(cau_hinh["sql_server"]),
            "-E",
            "-d",
            str(cau_hinh["ten_database"]),
            "-C",
            "-W",
            "-f",
            "65001",
            "-s",
            ky_tu_phan_tach,
            "-i",
            tep_sql_tam.name,
        ]

        ket_qua = subprocess.run(
            lenh,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return ket_qua.stdout
    finally:
        Path(tep_sql_tam.name).unlink(missing_ok=True)


def la_dong_gach_ngang_sqlcmd(dong: str, delimiter: str) -> bool:
    """Bỏ dòng -----|----- mà sqlcmd tự sinh sau header."""
    dong = dong.strip().replace(" ", "")

    if not dong:
        return False

    ky_tu_hop_le = {"-", delimiter}
    return set(dong) <= ky_tu_hop_le and "-" in dong


def tach_dong_sqlcmd(noi_dung: str, delimiter: str) -> list[list[str]]:
    dong_hop_le: list[list[str]] = []

    for dong in noi_dung.splitlines():
        dong = dong.rstrip()

        if not dong:
            continue

        dong_thuong = dong.lower().strip()

        if dong_thuong.startswith("(") and "rows affected" in dong_thuong:
            continue

        if la_dong_gach_ngang_sqlcmd(dong, delimiter):
            continue

        dong_hop_le.append(
            next(
                csv.reader(
                    [dong],
                    delimiter=delimiter,
                    quotechar='"',
                    escapechar="\\",
                )
            )
        )

    return dong_hop_le


def xuat_du_lieu_tu_sql(cau_hinh: dict[str, Any]) -> Path:
    duong_dan_du_lieu = Path(cau_hinh["duong_dan_du_lieu"])
    xuat_lai = bool(cau_hinh.get("xuat_lai_du_lieu", True))
    delimiter = str(cau_hinh.get("ky_tu_phan_tach", "|"))

    if duong_dan_du_lieu.exists() and not xuat_lai:
        return duong_dan_du_lieu

    duong_dan_du_lieu.parent.mkdir(parents=True, exist_ok=True)

    try:
        noi_dung = chay_lenh_sqlcmd(cau_hinh)
    except FileNotFoundError as loi:
        raise RuntimeError(
            "Không tìm thấy sqlcmd. Hãy cài SQL Server Command Line Utilities "
            "hoặc xuất dữ liệu thủ công bằng ai/sql/xuat_du_lieu_train.sql."
        ) from loi
    except subprocess.CalledProcessError as loi:
        thong_bao = loi.stderr or loi.stdout or str(loi)
        raise RuntimeError(
            "Không xuất được dữ liệu từ SQL Server bằng sqlcmd. "
            "Hãy kiểm tra sql_server, ten_database và quyền truy cập. "
            f"Chi tiết: {thong_bao}"
        ) from loi

    cac_dong = tach_dong_sqlcmd(noi_dung, delimiter)

    if len(cac_dong) < 2:
        raise RuntimeError("Không lấy được dữ liệu train từ SQL Server.")

    tieu_de, *du_lieu = cac_dong

    with duong_dan_du_lieu.open("w", encoding="utf-8", newline="") as tep:
        writer = csv.writer(
            tep,
            delimiter=delimiter,
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
            lineterminator="\n",
        )
        writer.writerow(tieu_de)
        writer.writerows(du_lieu)

    return duong_dan_du_lieu


def doc_json_an_toan(gia_tri: Any) -> dict[str, Any]:
    if not isinstance(gia_tri, str) or not gia_tri.strip():
        return {}

    try:
        ket_qua = json.loads(gia_tri)
        return ket_qua if isinstance(ket_qua, dict) else {}
    except json.JSONDecodeError:
        return {}


def chuyen_float_an_toan(gia_tri: Any, mac_dinh: float = 0.0) -> float:
    try:
        if gia_tri is None:
            return mac_dinh

        chuoi = str(gia_tri).strip()

        if not chuoi or chuoi.lower() in {"nan", "none", "null"}:
            return mac_dinh

        return float(chuoi)
    except (TypeError, ValueError):
        return mac_dinh


def diem_loi_ma_hoa(gia_tri: str) -> int:
    ky_tu_loi = ("Ã", "Ä", "Â", "Æ", "Å", "á", "à", "º", "»")
    diem = sum(gia_tri.count(ky_tu) for ky_tu in ky_tu_loi)
    diem += sum(1 for ky_tu in gia_tri if 0x80 <= ord(ky_tu) <= 0x9F)

    return diem


def chuyen_chuoi_mojibake_ve_byte(gia_tri: str) -> bytes:
    ket_qua = bytearray()

    for ky_tu in gia_tri:
        ma_ky_tu = ord(ky_tu)

        if ma_ky_tu <= 255:
            ket_qua.append(ma_ky_tu)
            continue

        try:
            ket_qua.extend(ky_tu.encode("cp1252"))
        except UnicodeEncodeError:
            ket_qua.extend(ky_tu.encode("utf-8"))

    return bytes(ket_qua)


def sua_loi_ma_hoa_tieng_viet(gia_tri: Any) -> Any:
    if not isinstance(gia_tri, str) or not gia_tri:
        return gia_tri

    diem_ban_dau = diem_loi_ma_hoa(gia_tri)

    if diem_ban_dau == 0:
        return gia_tri

    try:
        da_sua = chuyen_chuoi_mojibake_ve_byte(gia_tri).decode("utf-8")
    except UnicodeDecodeError:
        return gia_tri

    if diem_loi_ma_hoa(da_sua) < diem_ban_dau:
        return da_sua

    return gia_tri


def sua_loi_ma_hoa_dataframe(du_lieu: pd.DataFrame) -> pd.DataFrame:
    cac_cot_van_ban = [
        "DrugCode",
        "ActiveName",
        "TradeName",
        "RouteId",
        "DiseaseCode",
        "DiseaseName",
        "LinkTypeCode",
        "ConfidenceLevelCode",
        "HoatChat",
        "CongDung",
        "TacDungPhu",
        "MoTaBenh",
        "TrieuChung",
        "ThuocDieuTriDaBiet",
    ]

    for ten_cot in cac_cot_van_ban:
        if ten_cot in du_lieu.columns:
            du_lieu[ten_cot] = du_lieu[ten_cot].map(
                sua_loi_ma_hoa_tieng_viet
            )

    return du_lieu


def chuan_hoa_van_ban(gia_tri: Any) -> str:
    chuoi = "" if gia_tri is None else str(gia_tri)
    chuoi = unicodedata.normalize("NFD", chuoi)
    chuoi = "".join(
        ky_tu
        for ky_tu in chuoi
        if unicodedata.category(ky_tu) != "Mn"
    )
    chuoi = chuoi.replace("đ", "d").replace("Đ", "D")
    chuoi = chuoi.replace("đ", "d").replace("Đ", "D")
    chuoi = chuoi.lower()
    chuoi = re.sub(r"[^a-z0-9]+", " ", chuoi)
    return re.sub(r"\s+", " ", chuoi).strip()


def tach_tu(gia_tri: Any) -> set[str]:
    van_ban = chuan_hoa_van_ban(gia_tri)

    if not van_ban:
        return set()

    tu_dung = {
        "dieu",
        "tri",
        "phong",
        "ngua",
        "benh",
        "va",
        "do",
        "kem",
        "of",
        "the",
        "with",
        "in",
        "for",
        "to",
    }

    return {
        tu
        for tu in van_ban.split()
        if len(tu) > 1 and tu not in tu_dung
    }


def ti_le_tu_chung(
    van_ban_1: Any,
    van_ban_2: Any,
) -> tuple[int, float]:
    tap_1 = tach_tu(van_ban_1)
    tap_2 = tach_tu(van_ban_2)

    if not tap_1 or not tap_2:
        return 0, 0.0

    so_tu_chung = len(tap_1 & tap_2)
    mau_so = max(1, min(len(tap_1), len(tap_2)))

    return so_tu_chung, so_tu_chung / mau_so


def them_dac_trung_json(
    dac_trung: dict[str, Any],
    feature_json: dict[str, Any],
    loai_bo_ro_ri_nhan: bool,
) -> None:
    vector_x = feature_json.get("x")

    if isinstance(vector_x, list):
        for vi_tri, gia_tri in enumerate(vector_x):
            dac_trung[f"x_{vi_tri}"] = chuyen_float_an_toan(gia_tri)

    if loai_bo_ro_ri_nhan:
        return

    # Các trường dưới đây có thể mang thông tin gần với nhãn.
    # Chỉ dùng khi cố tình tắt loai_bo_dac_trung_ro_ri_nhan trong config.
    for ten_cot in [
        "source",
        "link_type",
        "evidence_field",
        "matched_keyword",
        "label_source",
        "note",
    ]:
        gia_tri = feature_json.get(ten_cot)

        if gia_tri is not None:
            dac_trung[f"json_{ten_cot}"] = str(gia_tri)


def tao_dac_trung(
    mau: pd.Series,
    loai_bo_ro_ri_nhan: bool = True,
    su_dung_dac_trung_dinh_danh: bool = True,
    su_dung_dac_trung_trung_khop_truc_tiep: bool = True,
    su_dung_thuoc_dieu_tri_da_biet: bool = True,
    su_dung_tac_dung_phu: bool = True,
    che_do_dac_trung: str = "day_du",
) -> dict[str, Any]:
    feature_json = doc_json_an_toan(mau.get("FeatureVectorJson"))
    ten_thuoc = str(mau.get("ActiveName", "") or "")
    ten_benh = str(mau.get("DiseaseName", "") or "")
    hoat_chat = str(mau.get("HoatChat", "") or "")
    cong_dung = str(mau.get("CongDung", "") or "")
    tac_dung_phu = str(mau.get("TacDungPhu", "") or "")
    mo_ta_benh = str(mau.get("MoTaBenh", "") or "")
    trieu_chung = str(mau.get("TrieuChung", "") or "")
    thuoc_dieu_tri_da_biet = str(
        mau.get("ThuocDieuTriDaBiet", "") or ""
    )

    if not su_dung_thuoc_dieu_tri_da_biet:
        thuoc_dieu_tri_da_biet = ""

    if not su_dung_tac_dung_phu:
        tac_dung_phu = ""

    cong_dung_chuan = chuan_hoa_van_ban(cong_dung)
    ten_benh_chuan = chuan_hoa_van_ban(ten_benh)
    so_tu_chung_cong_dung_benh, ti_le_cong_dung_benh = (
        ti_le_tu_chung(cong_dung, ten_benh)
    )
    so_tu_chung_hoat_chat_benh, ti_le_hoat_chat_benh = (
        ti_le_tu_chung(hoat_chat, ten_benh)
    )
    so_tu_chung_tac_dung_phu_benh, ti_le_tac_dung_phu_benh = (
        ti_le_tu_chung(tac_dung_phu, ten_benh)
    )
    so_tu_chung_cong_dung_trieu_chung, ti_le_cong_dung_trieu_chung = (
        ti_le_tu_chung(cong_dung, trieu_chung)
    )
    so_tu_chung_cong_dung_mo_ta, ti_le_cong_dung_mo_ta = (
        ti_le_tu_chung(cong_dung, mo_ta_benh)
    )
    so_tu_chung_hoat_chat_trieu_chung, ti_le_hoat_chat_trieu_chung = (
        ti_le_tu_chung(hoat_chat, trieu_chung)
    )
    (
        so_tu_chung_tac_dung_phu_trieu_chung,
        ti_le_tac_dung_phu_trieu_chung,
    ) = ti_le_tu_chung(tac_dung_phu, trieu_chung)
    (
        so_tu_chung_ten_thuoc_thuoc_da_biet,
        ti_le_ten_thuoc_thuoc_da_biet,
    ) = ti_le_tu_chung(ten_thuoc, thuoc_dieu_tri_da_biet)
    (
        so_tu_chung_hoat_chat_thuoc_da_biet,
        ti_le_hoat_chat_thuoc_da_biet,
    ) = ti_le_tu_chung(hoat_chat, thuoc_dieu_tri_da_biet)

    dac_trung: dict[str, Any] = {
        "drug_group_id": str(mau.get("DrugGroupId", "") or ""),
        "route_id": str(mau.get("RouteId", "") or ""),
        "disease_group_id": str(mau.get("DiseaseGroupId", "") or ""),
        "do_dai_ten_thuoc": len(ten_thuoc),
        "do_dai_ten_benh": len(ten_benh),
        "do_dai_hoat_chat": len(hoat_chat),
        "do_dai_cong_dung": len(cong_dung),
        "do_dai_tac_dung_phu": len(tac_dung_phu),
        "do_dai_mo_ta_benh": len(mo_ta_benh),
        "do_dai_trieu_chung": len(trieu_chung),
        "so_chi_dinh_trong_cong_dung": (
            cong_dung.count(";") + 1
            if cong_dung.strip()
            else 0
        ),
        "so_tu_chung_hoat_chat_benh": so_tu_chung_hoat_chat_benh,
        "ti_le_tu_chung_hoat_chat_benh": ti_le_hoat_chat_benh,
        "so_tu_chung_tac_dung_phu_benh": so_tu_chung_tac_dung_phu_benh,
        "ti_le_tu_chung_tac_dung_phu_benh": ti_le_tac_dung_phu_benh,
        "so_tu_chung_cong_dung_trieu_chung": (
            so_tu_chung_cong_dung_trieu_chung
        ),
        "ti_le_tu_chung_cong_dung_trieu_chung": (
            ti_le_cong_dung_trieu_chung
        ),
        "so_tu_chung_cong_dung_mo_ta": so_tu_chung_cong_dung_mo_ta,
        "ti_le_tu_chung_cong_dung_mo_ta": ti_le_cong_dung_mo_ta,
        "so_tu_chung_hoat_chat_trieu_chung": (
            so_tu_chung_hoat_chat_trieu_chung
        ),
        "ti_le_tu_chung_hoat_chat_trieu_chung": (
            ti_le_hoat_chat_trieu_chung
        ),
        "so_tu_chung_tac_dung_phu_trieu_chung": (
            so_tu_chung_tac_dung_phu_trieu_chung
        ),
        "ti_le_tu_chung_tac_dung_phu_trieu_chung": (
            ti_le_tac_dung_phu_trieu_chung
        ),
        "so_tu_chung_ten_thuoc_thuoc_da_biet": (
            so_tu_chung_ten_thuoc_thuoc_da_biet
        ),
        "ti_le_tu_chung_ten_thuoc_thuoc_da_biet": (
            ti_le_ten_thuoc_thuoc_da_biet
        ),
        "so_tu_chung_hoat_chat_thuoc_da_biet": (
            so_tu_chung_hoat_chat_thuoc_da_biet
        ),
        "ti_le_tu_chung_hoat_chat_thuoc_da_biet": (
            ti_le_hoat_chat_thuoc_da_biet
        ),
        "so_tu_hoat_chat": len(tach_tu(hoat_chat)),
        "so_tu_cong_dung": len(tach_tu(cong_dung)),
        "so_tu_ten_benh": len(tach_tu(ten_benh)),
        "so_tu_trieu_chung": len(tach_tu(trieu_chung)),
        "so_tu_mo_ta_benh": len(tach_tu(mo_ta_benh)),
        "so_tu_thuoc_dieu_tri_da_biet": len(
            tach_tu(thuoc_dieu_tri_da_biet)
        ),
        "co_mo_ta_benh": int(bool(mo_ta_benh.strip())),
        "co_trieu_chung": int(bool(trieu_chung.strip())),
        "co_thuoc_dieu_tri_da_biet": int(
            bool(thuoc_dieu_tri_da_biet.strip())
        ),
    }

    if su_dung_dac_trung_dinh_danh:
        dac_trung.update(
            {
                "drug_id": int(mau["DrugId"]),
                "disease_id": int(mau["DiseaseId"]),
                "drug_code": str(mau.get("DrugCode", "") or ""),
                "disease_code": str(mau.get("DiseaseCode", "") or ""),
            }
        )

    if su_dung_dac_trung_trung_khop_truc_tiep:
        dac_trung.update(
            {
                "ten_benh_nam_trong_cong_dung": int(
                    bool(ten_benh_chuan)
                    and ten_benh_chuan in cong_dung_chuan
                ),
                "cong_dung_nam_trong_ten_benh": int(
                    bool(cong_dung_chuan)
                    and cong_dung_chuan in ten_benh_chuan
                ),
                "so_tu_chung_cong_dung_benh": (
                    so_tu_chung_cong_dung_benh
                ),
                "ti_le_tu_chung_cong_dung_benh": ti_le_cong_dung_benh,
            }
        )

    if not loai_bo_ro_ri_nhan:
        dac_trung["link_type_code"] = str(
            mau.get("LinkTypeCode", "UNKNOWN") or "UNKNOWN"
        )
        dac_trung["confidence_level_code"] = str(
            mau.get("ConfidenceLevelCode", "UNKNOWN") or "UNKNOWN"
        )
        dac_trung["source_score"] = chuyen_float_an_toan(
            mau.get("SourceScore")
        )

    them_dac_trung_json(
        dac_trung,
        feature_json,
        loai_bo_ro_ri_nhan,
    )

    return loc_dac_trung_theo_che_do(dac_trung, che_do_dac_trung)


def loc_dac_trung_theo_che_do(
    dac_trung: dict[str, Any],
    che_do_dac_trung: str,
) -> dict[str, Any]:
    che_do = (che_do_dac_trung or "day_du").strip().lower()

    if che_do == "day_du":
        return dac_trung

    if che_do == "overlap_va_nhom":
        ket_qua: dict[str, Any] = {}

        for ten, gia_tri in dac_trung.items():
            if ten in {"drug_group_id", "route_id", "disease_group_id"}:
                ket_qua[ten] = gia_tri
            elif "tu_chung" in ten or ten.startswith("ti_le_"):
                ket_qua[ten] = gia_tri

        return ket_qua

    raise RuntimeError(
        "che_do_dac_trung chi ho tro 'day_du' hoac 'overlap_va_nhom'."
    )


def chuan_bi_du_lieu(
    duong_dan_du_lieu: str | Path,
    separator: str = "|",
) -> pd.DataFrame:
    du_lieu = pd.read_csv(
        duong_dan_du_lieu,
        sep=separator,
        engine="python",
        quotechar='"',
        encoding="utf-8",
        encoding_errors="replace",
    )

    cot_bat_buoc = [
        "DatasetItemId",
        "DrugId",
        "DiseaseId",
        "LabelValue",
        "SplitName",
        "FeatureVectorJson",
    ]

    cot_thieu = [
        cot for cot in cot_bat_buoc
        if cot not in du_lieu.columns
    ]

    if cot_thieu:
        raise RuntimeError(
            "File dữ liệu train thiếu cột bắt buộc: "
            + ", ".join(cot_thieu)
        )

    du_lieu = du_lieu[
        pd.to_numeric(
            du_lieu["DatasetItemId"],
            errors="coerce",
        ).notna()
    ].copy()

    if du_lieu.empty:
        raise RuntimeError("File dữ liệu train không có dòng dữ liệu hợp lệ.")

    du_lieu = sua_loi_ma_hoa_dataframe(du_lieu)

    du_lieu["DatasetItemId"] = du_lieu["DatasetItemId"].astype(int)
    du_lieu["DrugId"] = du_lieu["DrugId"].astype(int)
    du_lieu["DiseaseId"] = du_lieu["DiseaseId"].astype(int)
    du_lieu["LabelValue"] = du_lieu["LabelValue"].astype(int)
    du_lieu["SplitName"] = (
        du_lieu["SplitName"]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    cac_nhan = set(du_lieu["LabelValue"].unique().tolist())

    if not cac_nhan <= {0, 1}:
        raise RuntimeError(
            f"LabelValue chỉ được là 0 hoặc 1. Đang có: {cac_nhan}"
        )

    return du_lieu


def tach_theo_split(
    du_lieu: pd.DataFrame,
    ten_split: str,
) -> pd.DataFrame:
    ket_qua = du_lieu[du_lieu["SplitName"] == ten_split].copy()

    if ket_qua.empty:
        raise RuntimeError(f"Split {ten_split} không có dữ liệu.")

    return ket_qua


def phan_bo_nhan_theo_split(
    du_lieu: pd.DataFrame,
) -> dict[str, dict[str, int]]:
    bang = pd.crosstab(
        du_lieu["SplitName"],
        du_lieu["LabelValue"],
    )
    ket_qua: dict[str, dict[str, int]] = {}

    for ten_split, dong in bang.iterrows():
        ket_qua[str(ten_split)] = {
            str(nhan): int(so_luong)
            for nhan, so_luong in dong.items()
        }

    return ket_qua


def kiem_tra_du_2_lop(
    du_lieu: pd.DataFrame,
    ten_tap: str,
) -> None:
    so_lop = du_lieu["LabelValue"].nunique()

    if so_lop < 2:
        raise RuntimeError(
            f"Tập {ten_tap} chỉ có {so_lop} lớp nhãn. "
            "Không thể đánh giá mô hình nhị phân ổn định. "
            "Hãy tắt su_dung_split_database hoặc sửa lại SplitName trong DatasetItems."
        )


def chia_stratified(
    du_lieu: pd.DataFrame,
    cau_hinh: dict[str, Any],
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ti_le_validation = float(cau_hinh.get("ti_le_validation", 0.15))
    ti_le_test = float(cau_hinh.get("ti_le_test", 0.15))

    if ti_le_validation <= 0 or ti_le_test <= 0:
        raise RuntimeError("ti_le_validation và ti_le_test phải lớn hơn 0.")

    if ti_le_validation + ti_le_test >= 1:
        raise RuntimeError(
            "Tổng ti_le_validation + ti_le_test phải nhỏ hơn 1."
        )

    random_state = int(
        cau_hinh["tham_so_random_forest"].get("random_state", 42)
    )

    kiem_tra_du_2_lop(du_lieu, "ALL")

    nhan = du_lieu["LabelValue"].astype(int)

    du_lieu_train, du_lieu_tam = train_test_split(
        du_lieu,
        test_size=ti_le_validation + ti_le_test,
        random_state=random_state,
        stratify=nhan,
    )

    ti_le_test_trong_tam = ti_le_test / (
        ti_le_validation + ti_le_test
    )

    du_lieu_validation, du_lieu_test = train_test_split(
        du_lieu_tam,
        test_size=ti_le_test_trong_tam,
        random_state=random_state,
        stratify=du_lieu_tam["LabelValue"].astype(int),
    )

    return (
        du_lieu_train.copy(),
        du_lieu_validation.copy(),
        du_lieu_test.copy(),
    )


def tinh_metric(
    mo_hinh: Pipeline,
    du_lieu: pd.DataFrame,
    loai_bo_ro_ri_nhan: bool,
    su_dung_dac_trung_dinh_danh: bool,
    su_dung_dac_trung_trung_khop_truc_tiep: bool,
    su_dung_thuoc_dieu_tri_da_biet: bool,
    su_dung_tac_dung_phu: bool,
    che_do_dac_trung: str,
) -> dict[str, Any]:
    dac_trung = [
        tao_dac_trung(
            mau,
            loai_bo_ro_ri_nhan,
            su_dung_dac_trung_dinh_danh,
            su_dung_dac_trung_trung_khop_truc_tiep,
            su_dung_thuoc_dieu_tri_da_biet,
            su_dung_tac_dung_phu,
            che_do_dac_trung,
        )
        for _, mau in du_lieu.iterrows()
    ]

    nhan_dung = du_lieu["LabelValue"].astype(int)
    nhan_du_doan = mo_hinh.predict(dac_trung)
    xac_suat = mo_hinh.predict_proba(dac_trung)[:, 1]
    co_du_2_lop = len(set(nhan_dung)) == 2

    return {
        "so_mau": int(len(du_lieu)),
        "accuracy": float(
            accuracy_score(nhan_dung, nhan_du_doan)
        ),
        "precision": float(
            precision_score(
                nhan_dung,
                nhan_du_doan,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                nhan_dung,
                nhan_du_doan,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                nhan_dung,
                nhan_du_doan,
                zero_division=0,
            )
        ),
        "roc_auc": (
            float(roc_auc_score(nhan_dung, xac_suat))
            if co_du_2_lop
            else None
        ),
        "confusion_matrix": confusion_matrix(
            nhan_dung,
            nhan_du_doan,
            labels=[0, 1],
        ).tolist(),
        "classification_report": classification_report(
            nhan_dung,
            nhan_du_doan,
            output_dict=True,
            zero_division=0,
        ),
    }


def tao_pipeline(tham_so: dict[str, Any]) -> Pipeline:
    mo_hinh_random_forest = RandomForestClassifier(**tham_so)

    return Pipeline(
        steps=[
            ("ma_hoa_dac_trung", DictVectorizer(sparse=False)),
            ("random_forest", mo_hinh_random_forest),
        ]
    )


def luu_do_quan_trong_dac_trung(
    mo_hinh: Pipeline,
    duong_dan: str | Path,
) -> None:
    bo_ma_hoa: DictVectorizer = mo_hinh.named_steps[
        "ma_hoa_dac_trung"
    ]
    random_forest: RandomForestClassifier = mo_hinh.named_steps[
        "random_forest"
    ]

    ten_dac_trung = bo_ma_hoa.get_feature_names_out()
    do_quan_trong = random_forest.feature_importances_

    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    with duong_dan.open("w", encoding="utf-8", newline="") as tep:
        writer = csv.writer(tep)
        writer.writerow(["dac_trung", "do_quan_trong"])

        for ten, diem in sorted(
            zip(ten_dac_trung, do_quan_trong),
            key=lambda item: item[1],
            reverse=True,
        ):
            writer.writerow([ten, f"{diem:.10f}"])


def chuyen_dict_key_json_an_toan(
    gia_tri: dict[Any, Any],
) -> dict[str, Any]:
    return {
        str(khoa): int(gia_tri[khoa])
        for khoa in sorted(gia_tri)
    }


def chon_benh_am_kho(
    mau_duong: pd.Series,
    benh_theo_nhom: dict[str, list[pd.Series]],
    tat_ca_benh: list[pd.Series],
    cap_duong: set[tuple[int, int]],
) -> pd.Series | None:
    thuoc_id = int(mau_duong["DrugId"])
    benh_id = int(mau_duong["DiseaseId"])
    nhom_benh_id = str(mau_duong.get("DiseaseGroupId", "") or "")
    cong_dung = mau_duong.get("CongDung", "")

    ung_vien = [
        benh
        for benh in benh_theo_nhom.get(nhom_benh_id, [])
        if int(benh["DiseaseId"]) != benh_id
        and (thuoc_id, int(benh["DiseaseId"])) not in cap_duong
    ]

    if not ung_vien:
        ung_vien = [
            benh
            for benh in tat_ca_benh
            if int(benh["DiseaseId"]) != benh_id
            and (thuoc_id, int(benh["DiseaseId"])) not in cap_duong
        ]

    if not ung_vien:
        return None

    def diem_kho(benh: pd.Series) -> tuple[float, int]:
        _, ti_le = ti_le_tu_chung(cong_dung, benh.get("DiseaseName", ""))
        return ti_le, -int(benh["DiseaseId"])

    return max(ung_vien, key=diem_kho)


def tao_mau_am_kho(du_lieu: pd.DataFrame) -> pd.DataFrame:
    mau_duong = du_lieu[du_lieu["LabelValue"].astype(int) == 1].copy()
    benh = (
        mau_duong.sort_values("DiseaseId")
        .drop_duplicates("DiseaseId")
        .copy()
    )
    tat_ca_benh = [dong for _, dong in benh.iterrows()]
    benh_theo_nhom: dict[str, list[pd.Series]] = {}

    for _, dong in benh.iterrows():
        nhom = str(dong.get("DiseaseGroupId", "") or "")
        benh_theo_nhom.setdefault(nhom, []).append(dong)

    cap_duong = {
        (int(dong["DrugId"]), int(dong["DiseaseId"]))
        for _, dong in mau_duong.iterrows()
    }

    mau_am: list[pd.Series] = []
    for _, dong in mau_duong.iterrows():
        benh_am = chon_benh_am_kho(
            dong,
            benh_theo_nhom,
            tat_ca_benh,
            cap_duong,
        )

        if benh_am is None:
            continue

        dong_am = dong.copy()
        dong_am["DatasetItemId"] = int(dong["DatasetItemId"]) + 300000000
        dong_am["DiseaseId"] = int(benh_am["DiseaseId"])
        dong_am["LabelValue"] = 0
        dong_am["DiseaseGroupId"] = benh_am.get("DiseaseGroupId", "")
        dong_am["DiseaseCode"] = benh_am.get("DiseaseCode", "")
        dong_am["DiseaseName"] = benh_am.get("DiseaseName", "")
        dong_am["MoTaBenh"] = benh_am.get("MoTaBenh", "")
        dong_am["TrieuChung"] = benh_am.get("TrieuChung", "")
        dong_am["ThuocDieuTriDaBiet"] = benh_am.get(
            "ThuocDieuTriDaBiet",
            "",
        )
        dong_am["LinkTypeCode"] = "UNKNOWN"
        dong_am["ConfidenceLevelCode"] = "UNKNOWN"
        dong_am["SourceScore"] = ""
        mau_am.append(dong_am)

    if not mau_am:
        raise RuntimeError("Khong tao duoc mau am kho tu du lieu hien tai.")

    return pd.concat([mau_duong, pd.DataFrame(mau_am)], ignore_index=True)


def train(cau_hinh: dict[str, Any]) -> dict[str, Any]:
    delimiter = str(cau_hinh.get("ky_tu_phan_tach", "|"))

    duong_dan_du_lieu = xuat_du_lieu_tu_sql(cau_hinh)
    du_lieu = chuan_bi_du_lieu(
        duong_dan_du_lieu,
        delimiter,
    )

    su_dung_mau_am_kho = bool(
        cau_hinh.get("su_dung_mau_am_kho", False)
    )

    if su_dung_mau_am_kho:
        du_lieu = tao_mau_am_kho(du_lieu)

    loai_bo_ro_ri_nhan = bool(
        cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True)
    )
    su_dung_dac_trung_dinh_danh = bool(
        cau_hinh.get("su_dung_dac_trung_dinh_danh", True)
    )
    su_dung_dac_trung_trung_khop_truc_tiep = bool(
        cau_hinh.get("su_dung_dac_trung_trung_khop_truc_tiep", True)
    )
    su_dung_thuoc_dieu_tri_da_biet = bool(
        cau_hinh.get("su_dung_thuoc_dieu_tri_da_biet", True)
    )
    su_dung_tac_dung_phu = bool(
        cau_hinh.get("su_dung_tac_dung_phu", True)
    )
    che_do_dac_trung = str(cau_hinh.get("che_do_dac_trung", "day_du"))

    if cau_hinh.get("su_dung_split_database", False):
        du_lieu_train = tach_theo_split(du_lieu, "TRAIN")
        du_lieu_validation = tach_theo_split(du_lieu, "VALIDATION")
        du_lieu_test = tach_theo_split(du_lieu, "TEST")

        kiem_tra_du_2_lop(du_lieu_train, "TRAIN")
        kiem_tra_du_2_lop(du_lieu_validation, "VALIDATION")
        kiem_tra_du_2_lop(du_lieu_test, "TEST")

        cach_chia = "database_split"
    else:
        du_lieu_train, du_lieu_validation, du_lieu_test = (
            chia_stratified(
                du_lieu,
                cau_hinh,
            )
        )
        cach_chia = "stratified_split"

    dac_trung_train = [
        tao_dac_trung(
            mau,
            loai_bo_ro_ri_nhan,
            su_dung_dac_trung_dinh_danh,
            su_dung_dac_trung_trung_khop_truc_tiep,
            su_dung_thuoc_dieu_tri_da_biet,
            su_dung_tac_dung_phu,
            che_do_dac_trung,
        )
        for _, mau in du_lieu_train.iterrows()
    ]

    nhan_train = du_lieu_train["LabelValue"].astype(int)

    mo_hinh = tao_pipeline(cau_hinh["tham_so_random_forest"])
    mo_hinh.fit(dac_trung_train, nhan_train)

    bao_cao = {
        "database": cau_hinh["ten_database"],
        "duong_dan_du_lieu": str(duong_dan_du_lieu),
        "so_mau": {
            "tong": int(len(du_lieu)),
            "train": int(len(du_lieu_train)),
            "validation": int(len(du_lieu_validation)),
            "test": int(len(du_lieu_test)),
        },
        "phan_bo_nhan": chuyen_dict_key_json_an_toan(
            du_lieu["LabelValue"]
            .value_counts()
            .sort_index()
            .to_dict()
        ),
        "phan_bo_nhan_theo_split_database": (
            phan_bo_nhan_theo_split(du_lieu)
        ),
        "cach_chia_du_lieu_da_dung": cach_chia,
        "tham_so_random_forest": cau_hinh["tham_so_random_forest"],
        "loai_bo_dac_trung_ro_ri_nhan": loai_bo_ro_ri_nhan,
        "su_dung_mau_am_kho": su_dung_mau_am_kho,
        "su_dung_dac_trung_dinh_danh": su_dung_dac_trung_dinh_danh,
        "su_dung_dac_trung_trung_khop_truc_tiep": (
            su_dung_dac_trung_trung_khop_truc_tiep
        ),
        "su_dung_thuoc_dieu_tri_da_biet": (
            su_dung_thuoc_dieu_tri_da_biet
        ),
        "su_dung_tac_dung_phu": su_dung_tac_dung_phu,
        "che_do_dac_trung": che_do_dac_trung,
        "metric_validation": tinh_metric(
            mo_hinh,
            du_lieu_validation,
            loai_bo_ro_ri_nhan,
            su_dung_dac_trung_dinh_danh,
            su_dung_dac_trung_trung_khop_truc_tiep,
            su_dung_thuoc_dieu_tri_da_biet,
            su_dung_tac_dung_phu,
            che_do_dac_trung,
        ),
        "metric_test": tinh_metric(
            mo_hinh,
            du_lieu_test,
            loai_bo_ro_ri_nhan,
            su_dung_dac_trung_dinh_danh,
            su_dung_dac_trung_trung_khop_truc_tiep,
            su_dung_thuoc_dieu_tri_da_biet,
            su_dung_tac_dung_phu,
            che_do_dac_trung,
        ),
    }

    duong_dan_model = Path(cau_hinh["duong_dan_model"])
    duong_dan_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(mo_hinh, duong_dan_model)

    duong_dan_bao_cao = Path(cau_hinh["duong_dan_bao_cao"])
    duong_dan_bao_cao.parent.mkdir(parents=True, exist_ok=True)

    with duong_dan_bao_cao.open("w", encoding="utf-8") as tep:
        json.dump(
            bao_cao,
            tep,
            ensure_ascii=False,
            indent=2,
        )

    luu_do_quan_trong_dac_trung(
        mo_hinh,
        cau_hinh["duong_dan_do_quan_trong_dac_trung"],
    )

    return bao_cao


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Train RandomForest cho liên kết thuốc - bệnh."
    )
    parser.add_argument(
        "--config",
        default="ai/config/random_forest.json",
        help="Đường dẫn file cấu hình JSON.",
    )
    args = parser.parse_args()

    cau_hinh = doc_cau_hinh(args.config)
    bao_cao = train(cau_hinh)

    print("Train RandomForest thành công.")
    print(f"Tổng mẫu: {bao_cao['so_mau']['tong']}")
    print(f"Validation F1: {bao_cao['metric_validation']['f1']:.4f}")
    print(f"Test F1: {bao_cao['metric_test']['f1']:.4f}")

    test_roc_auc = bao_cao["metric_test"].get("roc_auc")

    if test_roc_auc is not None:
        print(f"Test ROC-AUC: {test_roc_auc:.4f}")
    else:
        print("Test ROC-AUC: không tính được vì tập test không đủ 2 lớp.")


if __name__ == "__main__":
    main()
