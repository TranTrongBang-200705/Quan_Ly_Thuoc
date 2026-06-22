from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit, train_test_split

from ai.src.train_random_forest import (
    chuan_bi_du_lieu,
    doc_cau_hinh,
    tao_dac_trung,
    tao_pipeline,
    ti_le_tu_chung,
)


def tao_dac_trung_dataframe(
    du_lieu: pd.DataFrame,
    cau_hinh: dict[str, Any],
    su_dung_trung_khop_truc_tiep: bool,
) -> list[dict[str, Any]]:
    return [
        tao_dac_trung(
            mau,
            bool(cau_hinh.get("loai_bo_dac_trung_ro_ri_nhan", True)),
            bool(cau_hinh.get("su_dung_dac_trung_dinh_danh", False)),
            su_dung_trung_khop_truc_tiep,
        )
        for _, mau in du_lieu.iterrows()
    ]


def tinh_metric_tu_du_lieu(
    du_lieu_train: pd.DataFrame,
    du_lieu_test: pd.DataFrame,
    cau_hinh: dict[str, Any],
    su_dung_trung_khop_truc_tiep: bool,
    so_cay_danh_gia: int,
) -> tuple[dict[str, Any], Any]:
    dac_trung_train = tao_dac_trung_dataframe(
        du_lieu_train,
        cau_hinh,
        su_dung_trung_khop_truc_tiep,
    )
    nhan_train = du_lieu_train["LabelValue"].astype(int)

    tham_so = dict(cau_hinh["tham_so_random_forest"])
    tham_so["n_estimators"] = so_cay_danh_gia
    mo_hinh = tao_pipeline(tham_so)
    mo_hinh.fit(dac_trung_train, nhan_train)

    dac_trung_test = tao_dac_trung_dataframe(
        du_lieu_test,
        cau_hinh,
        su_dung_trung_khop_truc_tiep,
    )
    nhan_dung = du_lieu_test["LabelValue"].astype(int)
    nhan_du_doan = mo_hinh.predict(dac_trung_test)
    xac_suat = mo_hinh.predict_proba(dac_trung_test)[:, 1]

    metric = {
        "so_cay_danh_gia": int(so_cay_danh_gia),
        "so_mau_train": int(len(du_lieu_train)),
        "so_mau_test": int(len(du_lieu_test)),
        "phan_bo_nhan_train": {
            str(khoa): int(gia_tri)
            for khoa, gia_tri in nhan_train.value_counts().sort_index().items()
        },
        "phan_bo_nhan_test": {
            str(khoa): int(gia_tri)
            for khoa, gia_tri in nhan_dung.value_counts().sort_index().items()
        },
        "accuracy": float(accuracy_score(nhan_dung, nhan_du_doan)),
        "precision": float(
            precision_score(nhan_dung, nhan_du_doan, zero_division=0)
        ),
        "recall": float(
            recall_score(nhan_dung, nhan_du_doan, zero_division=0)
        ),
        "f1": float(f1_score(nhan_dung, nhan_du_doan, zero_division=0)),
        "roc_auc": float(roc_auc_score(nhan_dung, xac_suat)),
        "confusion_matrix": confusion_matrix(
            nhan_dung,
            nhan_du_doan,
            labels=[0, 1],
        ).tolist(),
    }

    return metric, mo_hinh


def chia_ngau_nhien(
    du_lieu: pd.DataFrame,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    train, test = train_test_split(
        du_lieu,
        test_size=0.3,
        random_state=random_state,
        stratify=du_lieu["LabelValue"].astype(int),
    )
    return train.copy(), test.copy()


def chia_theo_nhom(
    du_lieu: pd.DataFrame,
    ten_cot_nhom: str,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    for thu_lai in range(20):
        splitter = GroupShuffleSplit(
            n_splits=1,
            test_size=0.3,
            random_state=random_state + thu_lai,
        )
        train_index, test_index = next(
            splitter.split(
                du_lieu,
                groups=du_lieu[ten_cot_nhom].astype(str),
            )
        )
        train = du_lieu.iloc[train_index].copy()
        test = du_lieu.iloc[test_index].copy()

        if (
            train["LabelValue"].nunique() == 2
            and test["LabelValue"].nunique() == 2
        ):
            return train, test

    raise RuntimeError(
        f"Khong chia duoc tap train/test du 2 lop theo {ten_cot_nhom}."
    )


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

    return pd.concat([mau_duong, pd.DataFrame(mau_am)], ignore_index=True)


def top_dac_trung(mo_hinh: Any, so_luong: int = 10) -> list[dict[str, Any]]:
    bo_ma_hoa = mo_hinh.named_steps["ma_hoa_dac_trung"]
    random_forest = mo_hinh.named_steps["random_forest"]

    ket_qua = []
    for ten, diem in sorted(
        zip(
            bo_ma_hoa.get_feature_names_out(),
            random_forest.feature_importances_,
        ),
        key=lambda item: item[1],
        reverse=True,
    )[:so_luong]:
        ket_qua.append({"dac_trung": str(ten), "do_quan_trong": float(diem)})

    return ket_qua


def danh_gia_kich_ban(
    ten_kich_ban: str,
    du_lieu: pd.DataFrame,
    cau_hinh: dict[str, Any],
    kieu_chia: str,
    su_dung_trung_khop_truc_tiep: bool,
    random_state: int,
    so_cay_danh_gia: int,
) -> dict[str, Any]:
    if kieu_chia == "ngau_nhien":
        train, test = chia_ngau_nhien(du_lieu, random_state)
    elif kieu_chia == "thuoc_moi":
        train, test = chia_theo_nhom(du_lieu, "DrugId", random_state)
    elif kieu_chia == "benh_moi":
        train, test = chia_theo_nhom(du_lieu, "DiseaseId", random_state)
    else:
        raise ValueError(f"Khong ho tro kieu chia: {kieu_chia}")

    metric, mo_hinh = tinh_metric_tu_du_lieu(
        train,
        test,
        cau_hinh,
        su_dung_trung_khop_truc_tiep,
        so_cay_danh_gia,
    )
    metric["ten_kich_ban"] = ten_kich_ban
    metric["kieu_chia"] = kieu_chia
    metric["su_dung_trung_khop_truc_tiep"] = su_dung_trung_khop_truc_tiep
    metric["top_dac_trung"] = top_dac_trung(mo_hinh)

    return metric


def ghi_bao_cao(ket_qua: list[dict[str, Any]], thu_muc_bao_cao: Path) -> None:
    thu_muc_bao_cao.mkdir(parents=True, exist_ok=True)
    duong_dan_json = thu_muc_bao_cao / "danh_gia_nghiem_khac_random_forest.json"
    duong_dan_csv = thu_muc_bao_cao / "danh_gia_nghiem_khac_random_forest.csv"

    with duong_dan_json.open("w", encoding="utf-8") as tep:
        json.dump(ket_qua, tep, ensure_ascii=False, indent=2)

    with duong_dan_csv.open("w", encoding="utf-8", newline="") as tep:
        writer = csv.writer(tep)
        writer.writerow(
            [
                "ten_kich_ban",
                "kieu_chia",
                "su_dung_trung_khop_truc_tiep",
                "so_mau_train",
                "so_mau_test",
                "accuracy",
                "precision",
                "recall",
                "f1",
                "roc_auc",
                "confusion_matrix",
            ]
        )

        for dong in ket_qua:
            writer.writerow(
                [
                    dong["ten_kich_ban"],
                    dong["kieu_chia"],
                    dong["su_dung_trung_khop_truc_tiep"],
                    dong["so_mau_train"],
                    dong["so_mau_test"],
                    f"{dong['accuracy']:.6f}",
                    f"{dong['precision']:.6f}",
                    f"{dong['recall']:.6f}",
                    f"{dong['f1']:.6f}",
                    f"{dong['roc_auc']:.6f}",
                    json.dumps(dong["confusion_matrix"]),
                ]
            )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Đánh giá RandomForest bằng các split nghiêm khắc hơn."
    )
    parser.add_argument("--config", default="ai/config/random_forest.json")
    parser.add_argument(
        "--so-cay-danh-gia",
        type=int,
        default=80,
        help="Số cây RandomForest dùng cho đánh giá phụ. Model chính không bị đổi.",
    )
    parser.add_argument(
        "--chi-kich-ban",
        default="",
        help="Chỉ chạy các kịch bản có tên chứa chuỗi này.",
    )
    args = parser.parse_args()

    cau_hinh = doc_cau_hinh(args.config)
    random_state = int(
        cau_hinh["tham_so_random_forest"].get("random_state", 42)
    )
    du_lieu = chuan_bi_du_lieu(
        cau_hinh["duong_dan_du_lieu"],
        str(cau_hinh.get("ky_tu_phan_tach", "|")),
    )
    du_lieu_am_kho = tao_mau_am_kho(du_lieu)

    cac_kich_ban = [
        (
            "random_split_co_trung_khop_truc_tiep",
            du_lieu,
            "ngau_nhien",
            True,
        ),
        (
            "random_split_bo_trung_khop_truc_tiep",
            du_lieu,
            "ngau_nhien",
            False,
        ),
        ("thuoc_moi_co_trung_khop_truc_tiep", du_lieu, "thuoc_moi", True),
        ("benh_moi_co_trung_khop_truc_tiep", du_lieu, "benh_moi", True),
        (
            "mau_am_kho_co_trung_khop_truc_tiep",
            du_lieu_am_kho,
            "ngau_nhien",
            True,
        ),
        (
            "mau_am_kho_bo_trung_khop_truc_tiep",
            du_lieu_am_kho,
            "ngau_nhien",
            False,
        ),
        (
            "mau_am_kho_thuoc_moi",
            du_lieu_am_kho,
            "thuoc_moi",
            True,
        ),
        (
            "mau_am_kho_benh_moi",
            du_lieu_am_kho,
            "benh_moi",
            True,
        ),
    ]

    if args.chi_kich_ban:
        cac_kich_ban = [
            kich_ban
            for kich_ban in cac_kich_ban
            if args.chi_kich_ban in kich_ban[0]
        ]

        if not cac_kich_ban:
            raise RuntimeError(
                f"Không tìm thấy kịch bản chứa: {args.chi_kich_ban}"
            )

    duong_dan_json = Path(
        "ai/reports/danh_gia_nghiem_khac_random_forest.json"
    )
    if args.chi_kich_ban and duong_dan_json.exists():
        ket_qua = json.loads(duong_dan_json.read_text(encoding="utf-8"))
        ten_da_co = {
            str(dong.get("ten_kich_ban"))
            for dong in ket_qua
        }
        ket_qua = [
            dong
            for dong in ket_qua
            if str(dong.get("ten_kich_ban")) not in ten_da_co
            or args.chi_kich_ban not in str(dong.get("ten_kich_ban"))
        ]
    else:
        ket_qua = []
    for ten, du_lieu_kich_ban, kieu_chia, dung_trung_khop in cac_kich_ban:
        print(f"Đang đánh giá: {ten}", flush=True)
        ket_qua_kich_ban = (
            danh_gia_kich_ban(
                ten,
                du_lieu_kich_ban,
                cau_hinh,
                kieu_chia,
                dung_trung_khop,
                random_state,
                args.so_cay_danh_gia,
            )
        )
        ket_qua.append(ket_qua_kich_ban)
        ghi_bao_cao(ket_qua, Path("ai/reports"))
        print(
            f"Xong {ten}: "
            f"F1={ket_qua_kich_ban['f1']:.4f}, "
            f"ROC-AUC={ket_qua_kich_ban['roc_auc']:.4f}",
            flush=True,
        )

    ghi_bao_cao(ket_qua, Path("ai/reports"))

    print("Đã tạo báo cáo đánh giá nghiêm khắc.")
    print("JSON: ai/reports/danh_gia_nghiem_khac_random_forest.json")
    print("CSV: ai/reports/danh_gia_nghiem_khac_random_forest.csv")

    for dong in ket_qua:
        print(
            f"{dong['ten_kich_ban']}: "
            f"F1={dong['f1']:.4f}, ROC-AUC={dong['roc_auc']:.4f}"
        )


if __name__ == "__main__":
    main()
