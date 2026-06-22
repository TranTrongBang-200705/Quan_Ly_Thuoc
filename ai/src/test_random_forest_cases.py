from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from ai.src.train_random_forest import (
    chuan_bi_du_lieu,
    doc_cau_hinh,
    tao_dac_trung,
)


def du_doan_xac_suat(
    mo_hinh: Any,
    du_lieu: pd.DataFrame,
    loai_bo_ro_ri_nhan: bool,
    su_dung_dac_trung_dinh_danh: bool,
    su_dung_dac_trung_trung_khop_truc_tiep: bool,
) -> pd.DataFrame:
    dac_trung = [
        tao_dac_trung(
            mau,
            loai_bo_ro_ri_nhan,
            su_dung_dac_trung_dinh_danh,
            su_dung_dac_trung_trung_khop_truc_tiep,
        )
        for _, mau in du_lieu.iterrows()
    ]

    random_forest = mo_hinh.named_steps["random_forest"]
    cac_lop = list(random_forest.classes_)

    if 1 not in cac_lop:
        raise RuntimeError(
            "Model khong co lop duong LabelValue = 1."
        )

    vi_tri_lop_duong = cac_lop.index(1)

    ket_qua = du_lieu.copy()
    ket_qua["ProbabilityPositive"] = mo_hinh.predict_proba(dac_trung)[
        :,
        vi_tri_lop_duong,
    ]
    ket_qua["PredictedLabel"] = mo_hinh.predict(dac_trung).astype(int)
    ket_qua["IsMatched"] = (
        ket_qua["PredictedLabel"].astype(int)
        == ket_qua["LabelValue"].astype(int)
    )

    return ket_qua


def lay_mau_an_toan(
    du_lieu: pd.DataFrame,
    so_luong: int,
    random_state: int,
) -> pd.DataFrame:
    if len(du_lieu) <= so_luong:
        return du_lieu.copy()

    return du_lieu.sample(
        n=so_luong,
        random_state=random_state,
    ).copy()


def them_nhom_case(
    cac_case: list[pd.DataFrame],
    ten_nhom: str,
    du_lieu: pd.DataFrame,
) -> None:
    nhom = du_lieu.copy()
    nhom.insert(0, "CaseGroup", ten_nhom)
    cac_case.append(nhom)


def tao_case_test(
    du_lieu_da_du_doan: pd.DataFrame,
    so_case_moi_nhom: int,
    random_state: int,
) -> pd.DataFrame:
    mau_duong = du_lieu_da_du_doan[
        du_lieu_da_du_doan["LabelValue"] == 1
    ].copy()
    mau_am = du_lieu_da_du_doan[
        du_lieu_da_du_doan["LabelValue"] == 0
    ].copy()

    cac_case: list[pd.DataFrame] = []

    them_nhom_case(
        cac_case,
        "duong_ngau_nhien_da_biet_lien_ket",
        lay_mau_an_toan(
            mau_duong,
            so_case_moi_nhom,
            random_state,
        ),
    )
    them_nhom_case(
        cac_case,
        "am_ngau_nhien_chua_co_lien_ket",
        lay_mau_an_toan(
            mau_am,
            so_case_moi_nhom,
            random_state + 1,
        ),
    )
    them_nhom_case(
        cac_case,
        "duong_diem_cao_nhat",
        mau_duong
        .sort_values("ProbabilityPositive", ascending=False)
        .head(so_case_moi_nhom),
    )
    them_nhom_case(
        cac_case,
        "am_diem_thap_nhat",
        mau_am
        .sort_values("ProbabilityPositive", ascending=True)
        .head(so_case_moi_nhom),
    )
    them_nhom_case(
        cac_case,
        "duong_de_nham_nhat_diem_thap",
        mau_duong
        .sort_values("ProbabilityPositive", ascending=True)
        .head(so_case_moi_nhom),
    )
    them_nhom_case(
        cac_case,
        "am_de_nham_nhat_diem_cao",
        mau_am
        .sort_values("ProbabilityPositive", ascending=False)
        .head(so_case_moi_nhom),
    )

    return pd.concat(cac_case, ignore_index=True)


def tom_tat_theo_nhom(case_test: pd.DataFrame) -> dict[str, Any]:
    bao_cao: dict[str, Any] = {}

    for ten_nhom, nhom in case_test.groupby("CaseGroup"):
        bao_cao[str(ten_nhom)] = {
            "so_case": int(len(nhom)),
            "so_case_khop": int(nhom["IsMatched"].sum()),
            "ti_le_khop": float(nhom["IsMatched"].mean()),
            "xac_suat_duong_trung_binh": float(
                nhom["ProbabilityPositive"].mean()
            ),
            "xac_suat_duong_thap_nhat": float(
                nhom["ProbabilityPositive"].min()
            ),
            "xac_suat_duong_cao_nhat": float(
                nhom["ProbabilityPositive"].max()
            ),
        }

    return bao_cao


def xuat_csv(
    case_test: pd.DataFrame,
    duong_dan: str | Path,
) -> None:
    cot_can_xuat = [
        "CaseGroup",
        "DatasetItemId",
        "DrugId",
        "DiseaseId",
        "DrugCode",
        "DiseaseCode",
        "ActiveName",
        "DiseaseName",
        "LabelValue",
        "PredictedLabel",
        "ProbabilityPositive",
        "IsMatched",
    ]

    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    case_test[cot_can_xuat].to_csv(
        duong_dan,
        index=False,
        encoding="utf-8-sig",
        quoting=csv.QUOTE_MINIMAL,
    )


def xuat_json(
    bao_cao: dict[str, Any],
    duong_dan: str | Path,
) -> None:
    duong_dan = Path(duong_dan)
    duong_dan.parent.mkdir(parents=True, exist_ok=True)

    with duong_dan.open("w", encoding="utf-8") as tep:
        json.dump(
            bao_cao,
            tep,
            ensure_ascii=False,
            indent=2,
        )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Tao case test cho model RandomForest thuoc - benh."
    )
    parser.add_argument(
        "--config",
        default="ai/config/random_forest.json",
        help="Duong dan file cau hinh JSON.",
    )
    parser.add_argument(
        "--so-case-moi-nhom",
        type=int,
        default=8,
        help="So case can lay cho moi nhom test.",
    )
    parser.add_argument(
        "--csv-output",
        default="ai/reports/test_cases_random_forest.csv",
        help="Duong dan file CSV ket qua case test.",
    )
    parser.add_argument(
        "--json-output",
        default="ai/reports/test_cases_random_forest.json",
        help="Duong dan file JSON tom tat case test.",
    )

    args = parser.parse_args()
    cau_hinh = doc_cau_hinh(args.config)

    random_state = int(
        cau_hinh["tham_so_random_forest"].get("random_state", 42)
    )
    loai_bo_ro_ri_nhan = bool(
        cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True)
    )
    su_dung_dac_trung_dinh_danh = bool(
        cau_hinh.get("su_dung_dac_trung_dinh_danh", True)
    )
    su_dung_dac_trung_trung_khop_truc_tiep = bool(
        cau_hinh.get("su_dung_dac_trung_trung_khop_truc_tiep", True)
    )

    du_lieu = chuan_bi_du_lieu(
        cau_hinh["duong_dan_du_lieu"],
        cau_hinh.get("ky_tu_phan_tach", "|"),
    )
    mo_hinh = joblib.load(cau_hinh["duong_dan_model"])
    du_lieu_da_du_doan = du_doan_xac_suat(
        mo_hinh,
        du_lieu,
        loai_bo_ro_ri_nhan,
        su_dung_dac_trung_dinh_danh,
        su_dung_dac_trung_trung_khop_truc_tiep,
    )
    case_test = tao_case_test(
        du_lieu_da_du_doan,
        args.so_case_moi_nhom,
        random_state,
    )
    bao_cao = {
        "model": cau_hinh["duong_dan_model"],
        "dataset": cau_hinh["duong_dan_du_lieu"],
        "so_case_moi_nhom": args.so_case_moi_nhom,
        "tong_so_case": int(len(case_test)),
        "ti_le_khop_toan_bo_case": float(case_test["IsMatched"].mean()),
        "su_dung_dac_trung_dinh_danh": su_dung_dac_trung_dinh_danh,
        "su_dung_dac_trung_trung_khop_truc_tiep": (
            su_dung_dac_trung_trung_khop_truc_tiep
        ),
        "tom_tat_theo_nhom": tom_tat_theo_nhom(case_test),
        "ghi_chu": (
            "LabelValue=1 la cap co lien ket trong database; "
            "LabelValue=0 la cap chua co lien ket duoc tao lam mau am. "
            "ProbabilityPositive la xac suat model du doan cap thuoc-benh co lien ket."
        ),
    }

    xuat_csv(case_test, args.csv_output)
    xuat_json(bao_cao, args.json_output)

    print("Da tao case test RandomForest.")
    print(f"Tong so case: {bao_cao['tong_so_case']}")
    print(
        "Ti le khop toan bo case: "
        f"{bao_cao['ti_le_khop_toan_bo_case']:.4f}"
    )
    print(f"CSV: {args.csv_output}")
    print(f"JSON: {args.json_output}")


if __name__ == "__main__":
    main()
