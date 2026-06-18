from __future__ import annotations

import argparse
import csv
import json
import subprocess
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
SELECT
    di.DatasetItemId,
    di.DrugId,
    di.DiseaseId,
    di.LabelValue,
    di.SplitName,
    REPLACE(REPLACE(COALESCE(di.FeatureVectorJson, N'{}'), CHAR(13), N' '), CHAR(10), N' ') AS FeatureVectorJson,
    COALESCE(dr.DrugCode, N'') AS DrugCode,
    COALESCE(dr.ActiveName, N'') AS ActiveName,
    COALESCE(dr.TradeName, N'') AS TradeName,
    COALESCE(CAST(dr.DrugGroupId AS nvarchar(30)), N'') AS DrugGroupId,
    COALESCE(CAST(dr.RouteId AS nvarchar(30)), N'') AS RouteId,
    COALESCE(CAST(dis.DiseaseGroupId AS nvarchar(30)), N'') AS DiseaseGroupId,
    COALESCE(dis.DiseaseCode, N'') AS DiseaseCode,
    COALESCE(dis.DiseaseName, N'') AS DiseaseName,
    COALESCE(lt.LinkTypeCode, N'UNKNOWN') AS LinkTypeCode,
    COALESCE(cl.LevelCode, N'UNKNOWN') AS ConfidenceLevelCode,
    COALESCE(CAST(src.SourceScore AS nvarchar(30)), N'') AS SourceScore
FROM dbo.DatasetItems di
JOIN dbo.Drugs dr ON dr.DrugId = di.DrugId
JOIN dbo.Diseases dis ON dis.DiseaseId = di.DiseaseId
LEFT JOIN dbo.DrugDiseaseLinks src ON src.LinkId = di.SourceLinkId
LEFT JOIN dbo.LinkTypes lt ON lt.LinkTypeId = src.LinkTypeId
LEFT JOIN dbo.ConfidenceLevels cl ON cl.ConfidenceLevelId = src.ConfidenceLevelId
ORDER BY di.DatasetItemId;
"""


def doc_cau_hinh(duong_dan: str | Path) -> dict[str, Any]:
    with Path(duong_dan).open("r", encoding="utf-8") as tep:
        return json.load(tep)


def chay_lenh_sqlcmd(cau_hinh: dict[str, Any]) -> str:
    lenh = [
        "sqlcmd",
        "-S",
        cau_hinh["sql_server"],
        "-E",
        "-d",
        cau_hinh["ten_database"],
        "-W",
        "-s",
        cau_hinh.get("ky_tu_phan_tach", "\t"),
        "-Q",
        CAU_LENH_LAY_DU_LIEU,
    ]
    ket_qua = subprocess.run(lenh, check=True, capture_output=True, text=True)
    return ket_qua.stdout


def tach_dong_sqlcmd(noi_dung: str) -> list[list[str]]:
    dong_hop_le: list[list[str]] = []
    for dong in noi_dung.splitlines():
        dong = dong.rstrip()
        if not dong:
            continue
        if dong.startswith("(") and "rows affected" in dong:
            continue
        if set(dong) <= {"-", "\t"}:
            continue
        dong_hop_le.append(next(csv.reader([dong], delimiter="\t")))
    return dong_hop_le


def xuat_du_lieu_tu_sql(cau_hinh: dict[str, Any]) -> Path:
    duong_dan_du_lieu = Path(cau_hinh["duong_dan_du_lieu"])
    if duong_dan_du_lieu.exists() and not cau_hinh.get("xuat_lai_du_lieu", True):
        return duong_dan_du_lieu

    duong_dan_du_lieu.parent.mkdir(parents=True, exist_ok=True)

    try:
        noi_dung = chay_lenh_sqlcmd(cau_hinh)
    except subprocess.CalledProcessError as loi:
        thong_bao = loi.stderr or loi.stdout or str(loi)
        raise RuntimeError(
            "Khong xuat duoc du lieu bang Python subprocess. "
            "Hay xuat TSV bang ai/sql/xuat_du_lieu_train.sql roi chay lai train."
        ) from RuntimeError(thong_bao)
    cac_dong = tach_dong_sqlcmd(noi_dung)
    if len(cac_dong) < 2:
        raise RuntimeError("Khong lay duoc du lieu train tu SQL Server.")

    tieu_de, *du_lieu = cac_dong
    with duong_dan_du_lieu.open("w", encoding="utf-8", newline="") as tep:
        writer = csv.writer(tep, delimiter=cau_hinh.get("ky_tu_phan_tach", "\t"))
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


def them_dac_trung_json(
    dac_trung: dict[str, Any],
    feature_json: dict[str, Any],
    loai_bo_ro_ri_nhan: bool,
) -> None:
    vector_x = feature_json.get("x")
    if isinstance(vector_x, list):
        for vi_tri, gia_tri in enumerate(vector_x):
            dac_trung[f"x_{vi_tri}"] = float(gia_tri or 0)

    if loai_bo_ro_ri_nhan:
        return

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


def tao_dac_trung(mau: pd.Series, loai_bo_ro_ri_nhan: bool = True) -> dict[str, Any]:
    feature_json = doc_json_an_toan(mau.get("FeatureVectorJson"))
    dac_trung: dict[str, Any] = {
        "drug_id": int(mau["DrugId"]),
        "disease_id": int(mau["DiseaseId"]),
        "drug_code": str(mau.get("DrugCode", "")),
        "disease_code": str(mau.get("DiseaseCode", "")),
        "drug_group_id": str(mau.get("DrugGroupId", "")),
        "route_id": str(mau.get("RouteId", "")),
        "disease_group_id": str(mau.get("DiseaseGroupId", "")),
        "do_dai_ten_thuoc": len(str(mau.get("ActiveName", ""))),
        "do_dai_ten_benh": len(str(mau.get("DiseaseName", ""))),
    }
    if not loai_bo_ro_ri_nhan:
        dac_trung["link_type_code"] = str(mau.get("LinkTypeCode", "UNKNOWN"))
        dac_trung["confidence_level_code"] = str(mau.get("ConfidenceLevelCode", "UNKNOWN"))
        dac_trung["source_score"] = (
            float(mau["SourceScore"]) if str(mau.get("SourceScore", "")).strip() else 0.0
        )
    them_dac_trung_json(dac_trung, feature_json, loai_bo_ro_ri_nhan)
    return dac_trung


def chuan_bi_du_lieu(duong_dan_du_lieu: str | Path) -> pd.DataFrame:
    du_lieu = pd.read_csv(
        duong_dan_du_lieu,
        sep="|",
        engine="python",
        quoting=csv.QUOTE_NONE,
        encoding="utf-8",
        encoding_errors="replace",
    )
    du_lieu = du_lieu[
        pd.to_numeric(du_lieu["DatasetItemId"], errors="coerce").notna()
    ].copy()
    du_lieu["LabelValue"] = du_lieu["LabelValue"].astype(int)
    du_lieu["SplitName"] = du_lieu["SplitName"].str.upper().str.strip()
    return du_lieu


def tach_theo_split(du_lieu: pd.DataFrame, ten_split: str) -> pd.DataFrame:
    ket_qua = du_lieu[du_lieu["SplitName"] == ten_split].copy()
    if ket_qua.empty:
        raise RuntimeError(f"Split {ten_split} khong co du lieu.")
    return ket_qua


def phan_bo_nhan_theo_split(du_lieu: pd.DataFrame) -> dict[str, dict[str, int]]:
    bang = pd.crosstab(du_lieu["SplitName"], du_lieu["LabelValue"])
    ket_qua: dict[str, dict[str, int]] = {}
    for ten_split, dong in bang.iterrows():
        ket_qua[str(ten_split)] = {str(nhan): int(so_luong) for nhan, so_luong in dong.items()}
    return ket_qua


def chia_stratified(du_lieu: pd.DataFrame, cau_hinh: dict[str, Any]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ti_le_validation = float(cau_hinh.get("ti_le_validation", 0.15))
    ti_le_test = float(cau_hinh.get("ti_le_test", 0.15))
    random_state = int(cau_hinh["tham_so_random_forest"].get("random_state", 42))
    nhan = du_lieu["LabelValue"].astype(int)

    du_lieu_train, du_lieu_tam = train_test_split(
        du_lieu,
        test_size=ti_le_validation + ti_le_test,
        random_state=random_state,
        stratify=nhan,
    )
    ti_le_test_trong_tam = ti_le_test / (ti_le_validation + ti_le_test)
    du_lieu_validation, du_lieu_test = train_test_split(
        du_lieu_tam,
        test_size=ti_le_test_trong_tam,
        random_state=random_state,
        stratify=du_lieu_tam["LabelValue"].astype(int),
    )
    return du_lieu_train.copy(), du_lieu_validation.copy(), du_lieu_test.copy()


def tinh_metric(mo_hinh: Pipeline, du_lieu: pd.DataFrame, loai_bo_ro_ri_nhan: bool) -> dict[str, Any]:
    dac_trung = [tao_dac_trung(mau, loai_bo_ro_ri_nhan) for _, mau in du_lieu.iterrows()]
    nhan_dung = du_lieu["LabelValue"].astype(int)
    nhan_du_doan = mo_hinh.predict(dac_trung)
    xac_suat = mo_hinh.predict_proba(dac_trung)[:, 1]
    co_du_2_lop = len(set(nhan_dung)) == 2
    return {
        "so_mau": int(len(du_lieu)),
        "accuracy": float(accuracy_score(nhan_dung, nhan_du_doan)),
        "precision": float(precision_score(nhan_dung, nhan_du_doan, zero_division=0)),
        "recall": float(recall_score(nhan_dung, nhan_du_doan, zero_division=0)),
        "f1": float(f1_score(nhan_dung, nhan_du_doan, zero_division=0)),
        "roc_auc": float(roc_auc_score(nhan_dung, xac_suat)) if co_du_2_lop else None,
        "confusion_matrix": confusion_matrix(nhan_dung, nhan_du_doan, labels=[0, 1]).tolist(),
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


def luu_do_quan_trong_dac_trung(mo_hinh: Pipeline, duong_dan: str | Path) -> None:
    bo_ma_hoa: DictVectorizer = mo_hinh.named_steps["ma_hoa_dac_trung"]
    random_forest: RandomForestClassifier = mo_hinh.named_steps["random_forest"]
    ten_dac_trung = bo_ma_hoa.get_feature_names_out()
    do_quan_trong = random_forest.feature_importances_

    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)
    with duong_dan.open("w", encoding="utf-8", newline="") as tep:
        writer = csv.writer(tep)
        writer.writerow(["dac_trung", "do_quan_trong"])
        for ten, diem in sorted(zip(ten_dac_trung, do_quan_trong), key=lambda item: item[1], reverse=True):
            writer.writerow([ten, f"{diem:.10f}"])


def train(cau_hinh: dict[str, Any]) -> dict[str, Any]:
    duong_dan_du_lieu = xuat_du_lieu_tu_sql(cau_hinh)
    du_lieu = chuan_bi_du_lieu(duong_dan_du_lieu)
    loai_bo_ro_ri_nhan = bool(cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True))
    if cau_hinh.get("su_dung_split_database", False):
        du_lieu_train = tach_theo_split(du_lieu, "TRAIN")
        du_lieu_validation = tach_theo_split(du_lieu, "VALIDATION")
        du_lieu_test = tach_theo_split(du_lieu, "TEST")
        cach_chia = "database_split"
    else:
        du_lieu_train, du_lieu_validation, du_lieu_test = chia_stratified(du_lieu, cau_hinh)
        cach_chia = "stratified_split"

    dac_trung_train = [tao_dac_trung(mau, loai_bo_ro_ri_nhan) for _, mau in du_lieu_train.iterrows()]
    nhan_train = du_lieu_train["LabelValue"].astype(int)

    mo_hinh = tao_pipeline(cau_hinh["tham_so_random_forest"])
    mo_hinh.fit(dac_trung_train, nhan_train)

    bao_cao = {
        "database": cau_hinh["ten_database"],
        "so_mau": {
            "tong": int(len(du_lieu)),
            "train": int(len(du_lieu_train)),
            "validation": int(len(du_lieu_validation)),
            "test": int(len(du_lieu_test)),
        },
        "phan_bo_nhan": du_lieu["LabelValue"].value_counts().sort_index().to_dict(),
        "phan_bo_nhan_theo_split_database": phan_bo_nhan_theo_split(du_lieu),
        "cach_chia_du_lieu_da_dung": cach_chia,
        "tham_so_random_forest": cau_hinh["tham_so_random_forest"],
        "loai_bo_dac_trung_ro_ri_nhan": loai_bo_ro_ri_nhan,
        "metric_validation": tinh_metric(mo_hinh, du_lieu_validation, loai_bo_ro_ri_nhan),
        "metric_test": tinh_metric(mo_hinh, du_lieu_test, loai_bo_ro_ri_nhan),
    }

    duong_dan_model = Path(cau_hinh["duong_dan_model"])
    duong_dan_model.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(mo_hinh, duong_dan_model)

    duong_dan_bao_cao = Path(cau_hinh["duong_dan_bao_cao"])
    duong_dan_bao_cao.parent.mkdir(parents=True, exist_ok=True)
    with duong_dan_bao_cao.open("w", encoding="utf-8") as tep:
        json.dump(bao_cao, tep, ensure_ascii=False, indent=2)

    luu_do_quan_trong_dac_trung(mo_hinh, cau_hinh["duong_dan_do_quan_trong_dac_trung"])
    return bao_cao


def main() -> None:
    parser = argparse.ArgumentParser(description="Train RandomForest cho lien ket thuoc - benh.")
    parser.add_argument("--config", default="ai/config/random_forest.json")
    args = parser.parse_args()

    cau_hinh = doc_cau_hinh(args.config)
    bao_cao = train(cau_hinh)

    print("Train RandomForest thanh cong.")
    print(f"Tong mau: {bao_cao['so_mau']['tong']}")
    print(f"Validation F1: {bao_cao['metric_validation']['f1']:.4f}")
    print(f"Test F1: {bao_cao['metric_test']['f1']:.4f}")
    print(f"Test ROC-AUC: {bao_cao['metric_test']['roc_auc']:.4f}")


if __name__ == "__main__":
    main()
