from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
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
        COALESCE(CAST(lk.DiemLienKet AS nvarchar(30)), N'') AS SourceScore
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
        N'' AS SourceScore
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
        "-Q",
        CAU_LENH_LAY_DU_LIEU,
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
) -> dict[str, Any]:
    feature_json = doc_json_an_toan(mau.get("FeatureVectorJson"))

    dac_trung: dict[str, Any] = {
        "drug_id": int(mau["DrugId"]),
        "disease_id": int(mau["DiseaseId"]),
        "drug_code": str(mau.get("DrugCode", "") or ""),
        "disease_code": str(mau.get("DiseaseCode", "") or ""),
        "drug_group_id": str(mau.get("DrugGroupId", "") or ""),
        "route_id": str(mau.get("RouteId", "") or ""),
        "disease_group_id": str(mau.get("DiseaseGroupId", "") or ""),
        "do_dai_ten_thuoc": len(str(mau.get("ActiveName", "") or "")),
        "do_dai_ten_benh": len(str(mau.get("DiseaseName", "") or "")),
    }

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

    return dac_trung


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
) -> dict[str, Any]:
    dac_trung = [
        tao_dac_trung(mau, loai_bo_ro_ri_nhan)
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


def train(cau_hinh: dict[str, Any]) -> dict[str, Any]:
    delimiter = str(cau_hinh.get("ky_tu_phan_tach", "|"))

    duong_dan_du_lieu = xuat_du_lieu_tu_sql(cau_hinh)
    du_lieu = chuan_bi_du_lieu(
        duong_dan_du_lieu,
        delimiter,
    )

    loai_bo_ro_ri_nhan = bool(
        cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True)
    )

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
        tao_dac_trung(mau, loai_bo_ro_ri_nhan)
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
        "metric_validation": tinh_metric(
            mo_hinh,
            du_lieu_validation,
            loai_bo_ro_ri_nhan,
        ),
        "metric_test": tinh_metric(
            mo_hinh,
            du_lieu_test,
            loai_bo_ro_ri_nhan,
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
