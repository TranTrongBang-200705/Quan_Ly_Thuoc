from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.db_models import (
    Benh,
    KetQuaDuDoan,
    LienKetThuocBenh,
    LoaiLienKet,
    MoHinhMayHoc,
    MucTinCay,
    Thuoc,
    User,
    YeuCauDuDoan,
)
from app.schemas.dto import PredictionCreateRequest
from app.services.ai_client import predict_batch as ai_predict_batch
from app.utils.exceptions import AppError

logger = logging.getLogger(__name__)

MEDICAL_WARNING = "Thong tin chi phuc vu hoc tap, nghien cuu va tham khao. Khong dung de tu chan doan, ke don hoac thay the tu van cua bac si/duoc si."
FALLBACK_WARNING = "AI service khong kha dung, he thong tam dung diem lien ket co san trong co so du lieu."
SOURCE_AI = "AI_MODEL"
SOURCE_FALLBACK = "DATABASE_FALLBACK"
SOURCE_UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class PredictionCandidate:
    thuoc: Thuoc
    benh: Benh
    link: LienKetThuocBenh | None = None
    loai: LoaiLienKet | None = None
    muc: MucTinCay | None = None


@dataclass(frozen=True)
class ScoredCandidate:
    candidate: PredictionCandidate
    score: float
    predicted_label: int | None
    source: str
    warning: str | None = None


def code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:24].upper()}"


def fmt(score: float) -> str:
    return f"{score:.5f}".rstrip("0").rstrip(".")


def clamp_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, score))


def normalize_prediction_type(value: str) -> str:
    raw = (value or "").strip().upper()
    mapping = {
        "DRUG_TO_DISEASE": "DRUG_TO_DISEASE",
        "THUOC_TIM_BENH": "DRUG_TO_DISEASE",
        "TU_THUOC_TIM_BENH": "DRUG_TO_DISEASE",
        "DISEASE_TO_DRUG": "DISEASE_TO_DRUG",
        "BENH_TIM_THUOC": "DISEASE_TO_DRUG",
        "TU_BENH_TIM_THUOC": "DISEASE_TO_DRUG",
        "PAIR_CHECK": "PAIR_PREDICTION",
        "PAIR_PREDICTION": "PAIR_PREDICTION",
        "KIEM_TRA_CAP": "PAIR_PREDICTION",
        "KIEM_TRA_CAP_THUOC_BENH": "PAIR_PREDICTION",
    }
    if raw not in mapping:
        raise AppError("Kieu du doan chi nhan DRUG_TO_DISEASE, DISEASE_TO_DRUG hoac PAIR_PREDICTION.")
    return mapping[raw]


def validate_request(req: PredictionCreateRequest) -> str:
    prediction_type = normalize_prediction_type(req.prediction_type)
    if not req.medical_warning_accepted:
        raise AppError("Vui long xac nhan canh bao y te truoc khi du doan.")
    if prediction_type == "DRUG_TO_DISEASE" and req.drug_id is None:
        raise AppError("Tu thuoc tim benh can nhap ThuocId.")
    if prediction_type == "DISEASE_TO_DRUG" and req.disease_id is None:
        raise AppError("Tu benh tim thuoc can nhap BenhId.")
    if prediction_type == "PAIR_PREDICTION" and (req.drug_id is None or req.disease_id is None):
        raise AppError("Kiem tra mot cap thuoc - benh can nhap ca ThuocId va BenhId.")
    return prediction_type


def get_thuoc_or_throw(db: Session, thuoc_id: int | None) -> Thuoc:
    if thuoc_id is None:
        raise AppError("Vui long nhap ThuocId.")
    thuoc = db.execute(select(Thuoc).where(Thuoc.thuoc_id == thuoc_id)).scalar_one_or_none()
    if thuoc is None:
        max_id = db.execute(select(func.max(Thuoc.thuoc_id))).scalar_one_or_none()
        raise AppError(f"ThuocId={thuoc_id} khong ton tai. ThuocId lon nhat hien co la {max_id or 0}.")
    return thuoc


def get_benh_or_throw(db: Session, benh_id: int | None) -> Benh:
    if benh_id is None:
        raise AppError("Vui long nhap BenhId.")
    benh = db.execute(select(Benh).where(Benh.benh_id == benh_id)).scalar_one_or_none()
    if benh is None:
        max_id = db.execute(select(func.max(Benh.benh_id))).scalar_one_or_none()
        raise AppError(f"BenhId={benh_id} khong ton tai. BenhId lon nhat hien co la {max_id or 0}.")
    return benh


def confidence_id(score: float, levels: list[MucTinCay]) -> int | None:
    for level in levels:
        min_score = float(level.diem_tu) if level.diem_tu is not None else None
        max_score = float(level.diem_den) if level.diem_den is not None else None
        if (min_score is None or score >= min_score) and (max_score is None or score <= max_score):
            return level.muc_tin_cay_id
    return None


def candidate_rows(db: Session, req: PredictionCreateRequest, prediction_type: str) -> list[PredictionCandidate]:
    if prediction_type == "DRUG_TO_DISEASE":
        thuoc = get_thuoc_or_throw(db, req.drug_id)
        rows = db.execute(
            select(Benh, LienKetThuocBenh, LoaiLienKet, MucTinCay)
            .select_from(Benh)
            .outerjoin(
                LienKetThuocBenh,
                and_(
                    LienKetThuocBenh.thuoc_id == thuoc.thuoc_id,
                    LienKetThuocBenh.benh_id == Benh.benh_id,
                ),
            )
            .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
            .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
            .order_by(Benh.ten_benh)
        ).all()
        return [PredictionCandidate(thuoc=thuoc, benh=benh, link=link, loai=loai, muc=muc) for benh, link, loai, muc in rows]

    if prediction_type == "DISEASE_TO_DRUG":
        benh = get_benh_or_throw(db, req.disease_id)
        rows = db.execute(
            select(Thuoc, LienKetThuocBenh, LoaiLienKet, MucTinCay)
            .select_from(Thuoc)
            .outerjoin(
                LienKetThuocBenh,
                and_(
                    LienKetThuocBenh.thuoc_id == Thuoc.thuoc_id,
                    LienKetThuocBenh.benh_id == benh.benh_id,
                ),
            )
            .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
            .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
            .order_by(Thuoc.ten_thuoc)
        ).all()
        return [PredictionCandidate(thuoc=thuoc, benh=benh, link=link, loai=loai, muc=muc) for thuoc, link, loai, muc in rows]

    thuoc = get_thuoc_or_throw(db, req.drug_id)
    benh = get_benh_or_throw(db, req.disease_id)
    row = db.execute(
        select(LienKetThuocBenh, LoaiLienKet, MucTinCay)
        .select_from(LienKetThuocBenh)
        .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
        .where(LienKetThuocBenh.thuoc_id == thuoc.thuoc_id, LienKetThuocBenh.benh_id == benh.benh_id)
    ).first()
    link, loai, muc = row if row else (None, None, None)
    return [PredictionCandidate(thuoc=thuoc, benh=benh, link=link, loai=loai, muc=muc)]


def ai_payload(candidates: list[PredictionCandidate]) -> list[dict[str, Any]]:
    return [
        {
            "thuocId": item.thuoc.thuoc_id,
            "benhId": item.benh.benh_id,
            "maThuoc": item.thuoc.ma_thuoc or "",
            "maBenh": item.benh.ma_benh or "",
            "nhomThuocId": item.thuoc.nhom_thuoc_id,
            "routeId": None,
            "nhomBenhId": item.benh.nhom_benh_id,
            "tenThuoc": item.thuoc.ten_thuoc or "",
            "tenBenh": item.benh.ten_benh or "",
        }
        for item in candidates
    ]


def score_key(value: dict[str, Any]) -> tuple[int, int] | None:
    thuoc_id = value.get("thuocId", value.get("drugId"))
    benh_id = value.get("benhId", value.get("diseaseId"))
    if thuoc_id is None or benh_id is None:
        return None
    return int(thuoc_id), int(benh_id)


def parse_ai_scores(response: dict[str, Any]) -> dict[tuple[int, int], tuple[float, int | None]]:
    scores: dict[tuple[int, int], tuple[float, int | None]] = {}
    for item in response.get("results", []):
        key = score_key(item)
        if key is None:
            continue
        score = clamp_score(item.get("diemDuDoan", item.get("predictionScore")))
        label = item.get("nhanDuDoan", item.get("predictedLabel"))
        scores[key] = (score, int(label) if label is not None else None)
    return scores


async def score_candidates(candidates: list[PredictionCandidate]) -> list[ScoredCandidate]:
    if not candidates:
        return []
    try:
        response = await ai_predict_batch(ai_payload(candidates))
        ai_scores = parse_ai_scores(response)
        return [
            ScoredCandidate(
                candidate=item,
                score=ai_scores.get((item.thuoc.thuoc_id, item.benh.benh_id), (0.0, None))[0],
                predicted_label=ai_scores.get((item.thuoc.thuoc_id, item.benh.benh_id), (0.0, None))[1],
                source=SOURCE_AI,
            )
            for item in candidates
        ]
    except AppError as exc:
        logger.warning("AI service unavailable, using database fallback: %s", exc)
        return [
            ScoredCandidate(
                candidate=item,
                score=clamp_score(item.link.diem_lien_ket if item.link else 0.0),
                predicted_label=1 if item.link else 0,
                source=SOURCE_FALLBACK,
                warning=FALLBACK_WARNING,
            )
            for item in candidates
        ]


def source_from_explanation(text: str | None) -> str:
    raw = (text or "").upper()
    if SOURCE_FALLBACK in raw:
        return SOURCE_FALLBACK
    if SOURCE_AI in raw:
        return SOURCE_AI
    return SOURCE_UNKNOWN


def result_dto(result: KetQuaDuDoan, thuoc: Thuoc, benh: Benh, muc: MucTinCay | None, loai: LoaiLienKet | None) -> dict:
    score = float(result.diem_du_doan)
    source = source_from_explanation(result.giai_thich_ngan)
    fallback_warning = FALLBACK_WARNING if source == SOURCE_FALLBACK else None
    return {
        "ketQuaDuDoanId": result.ket_qua_du_doan_id,
        "yeuCauDuDoanId": result.yeu_cau_du_doan_id,
        "thuHang": result.thu_hang,
        "thuocId": result.thuoc_id,
        "tenThuoc": thuoc.ten_thuoc,
        "duongDanAnh": thuoc.duong_dan_anh,
        "benhId": result.benh_id,
        "tenBenh": benh.ten_benh,
        "diemDuDoan": score,
        "nguonDiem": source,
        "nhanDuDoan": 1 if score >= 0.5 else 0,
        "tenMucTinCay": muc.ten_muc_tin_cay if muc else None,
        "tenLoaiLienKet": loai.ten_loai_lien_ket if loai else None,
        "giaiThichNgan": result.giai_thich_ngan,
        "canhBao": fallback_warning,
        "canhBaoYTe": result.canh_bao_y_te or MEDICAL_WARNING,
        "predictionResultId": result.ket_qua_du_doan_id,
        "rankNo": result.thu_hang,
        "drugId": result.thuoc_id,
        "drugName": thuoc.ten_thuoc,
        "drugImageUrl": thuoc.duong_dan_anh,
        "diseaseId": result.benh_id,
        "diseaseName": benh.ten_benh,
        "predictionScore": score,
        "scoreSource": source,
        "predictedLabel": 1 if score >= 0.5 else 0,
        "confidenceLevel": muc.ten_muc_tin_cay if muc else None,
        "linkType": loai.ten_loai_lien_ket if loai else None,
        "explanationText": result.giai_thich_ngan,
        "warningText": result.canh_bao_y_te or MEDICAL_WARNING,
        "systemWarning": fallback_warning,
    }


def explanation(scored: ScoredCandidate, model_name: str) -> str:
    item = scored.candidate
    if scored.source == SOURCE_FALLBACK:
        note = item.link.ghi_chu if item.link and item.link.ghi_chu else "Database fallback score from LienKetThuocBenh.DiemLienKet."
        return f"Nguon diem: {SOURCE_FALLBACK}. {FALLBACK_WARNING} {note}"
    note = item.link.ghi_chu if item.link and item.link.ghi_chu else "RandomForest scored this candidate pair from DataThuoc features."
    return f"Nguon diem: {SOURCE_AI}. Model: {model_name}. {note}"


async def create_prediction(db: Session, req: PredictionCreateRequest, user: User) -> dict:
    prediction_type = validate_request(req)
    threshold = float(req.score_threshold if req.score_threshold is not None else 0)
    top_k = max(1, min(int(req.top_k or 10), 100))
    candidates = candidate_rows(db, req, prediction_type)
    levels = db.execute(select(MucTinCay).order_by(MucTinCay.diem_tu.desc())).scalars().all()
    model = db.execute(select(MoHinhMayHoc).where(MoHinhMayHoc.dang_duoc_dung == True)).scalar_one_or_none()  # noqa: E712
    model_name = model.ten_mo_hinh if model else "RandomForest DataThuoc"

    request = YeuCauDuDoan(
        ma_yeu_cau=code("REQ"),
        nguoi_dung_id=user.user_id,
        kieu_du_doan=prediction_type,
        thuoc_dau_vao_id=None if prediction_type == "DISEASE_TO_DRUG" else req.drug_id,
        benh_dau_vao_id=None if prediction_type == "DRUG_TO_DISEASE" else req.disease_id,
        so_luong_ket_qua=top_k,
        nguong_diem=threshold,
        muc_dich=req.purpose.strip() if req.purpose else None,
        email_lien_he=str(req.contact_email).strip() if req.contact_email else None,
        da_chap_nhan_canh_bao_y_te=req.medical_warning_accepted,
        trang_thai_yeu_cau="Dang xu ly",
        ngay_tao=datetime.utcnow(),
    )
    db.add(request)
    db.flush()

    scored = await score_candidates(candidates)
    selected = [item for item in scored if item.score >= threshold]
    selected.sort(key=lambda item: item.score, reverse=True)
    selected = selected[:top_k]

    for rank, item in enumerate(selected, start=1):
        candidate = item.candidate
        score = round(item.score, 5)
        db.add(
            KetQuaDuDoan(
                yeu_cau_du_doan_id=request.yeu_cau_du_doan_id,
                thuoc_id=candidate.thuoc.thuoc_id,
                benh_id=candidate.benh.benh_id,
                thu_hang=rank,
                diem_du_doan=score,
                muc_tin_cay_id=candidate.muc.muc_tin_cay_id if candidate.muc else confidence_id(score, levels),
                loai_lien_ket_id=candidate.loai.loai_lien_ket_id if candidate.loai else None,
                giai_thich_ngan=explanation(item, model_name),
                canh_bao_y_te=MEDICAL_WARNING,
                ngay_tao=datetime.utcnow(),
            )
        )

    request.trang_thai_yeu_cau = "Hoan thanh"
    db.commit()
    response = get_prediction(db, request.yeu_cau_du_doan_id) or {}
    if any(item.source == SOURCE_FALLBACK for item in scored):
        response["nguonDiem"] = SOURCE_FALLBACK
        response["canhBao"] = FALLBACK_WARNING
    else:
        response["nguonDiem"] = SOURCE_AI
    return response


def get_prediction(db: Session, request_id: int) -> dict | None:
    request = db.execute(select(YeuCauDuDoan).where(YeuCauDuDoan.yeu_cau_du_doan_id == request_id)).scalar_one_or_none()
    if request is None:
        return None
    stmt = (
        select(KetQuaDuDoan, Thuoc, Benh, MucTinCay, LoaiLienKet)
        .join(Thuoc, KetQuaDuDoan.thuoc_id == Thuoc.thuoc_id)
        .join(Benh, KetQuaDuDoan.benh_id == Benh.benh_id)
        .outerjoin(MucTinCay, KetQuaDuDoan.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
        .outerjoin(LoaiLienKet, KetQuaDuDoan.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .where(KetQuaDuDoan.yeu_cau_du_doan_id == request_id)
        .order_by(KetQuaDuDoan.thu_hang)
    )
    results = [result_dto(*row) for row in db.execute(stmt).all()]
    source = results[0]["nguonDiem"] if results else SOURCE_UNKNOWN
    fallback = source == SOURCE_FALLBACK
    return {
        "yeuCauDuDoanId": request.yeu_cau_du_doan_id,
        "maYeuCau": request.ma_yeu_cau,
        "kieuDuDoan": request.kieu_du_doan,
        "trangThaiYeuCau": request.trang_thai_yeu_cau,
        "ngayTao": request.ngay_tao.isoformat() if request.ngay_tao else None,
        "nguongDiem": float(request.nguong_diem or 0),
        "nguonDiem": source,
        "canhBao": FALLBACK_WARNING if fallback else None,
        "resultMessage": f"Tim thay {len(results)} ket qua phu hop." if results else "Khong co ket qua phu hop voi nguong diem da chon.",
        "results": results,
        "requestId": request.yeu_cau_du_doan_id,
        "requestCode": request.ma_yeu_cau,
        "predictionRunId": request.yeu_cau_du_doan_id,
        "runCode": request.ma_yeu_cau,
        "requestStatus": request.trang_thai_yeu_cau,
        "createdAt": request.ngay_tao.isoformat() if request.ngay_tao else None,
        "scoreThreshold": float(request.nguong_diem or 0),
        "scoreSource": source,
        "systemWarning": FALLBACK_WARNING if fallback else None,
    }


def history(db: Session, user_id: int | None) -> list[dict]:
    stmt = (
        select(YeuCauDuDoan, Thuoc, Benh)
        .outerjoin(Thuoc, YeuCauDuDoan.thuoc_dau_vao_id == Thuoc.thuoc_id)
        .outerjoin(Benh, YeuCauDuDoan.benh_dau_vao_id == Benh.benh_id)
    )
    if user_id:
        stmt = stmt.where(YeuCauDuDoan.nguoi_dung_id == user_id)
    rows = db.execute(stmt.order_by(YeuCauDuDoan.ngay_tao.desc()).limit(100)).all()
    out = []
    for request, thuoc, benh in rows:
        count = db.execute(select(func.count(KetQuaDuDoan.ket_qua_du_doan_id)).where(KetQuaDuDoan.yeu_cau_du_doan_id == request.yeu_cau_du_doan_id)).scalar_one()
        out.append({
            "yeuCauDuDoanId": request.yeu_cau_du_doan_id,
            "maYeuCau": request.ma_yeu_cau,
            "kieuDuDoan": request.kieu_du_doan,
            "tenThuocDauVao": thuoc.ten_thuoc if thuoc else None,
            "tenBenhDauVao": benh.ten_benh if benh else None,
            "trangThaiYeuCau": request.trang_thai_yeu_cau,
            "soKetQua": count,
            "ngayTao": request.ngay_tao.isoformat() if request.ngay_tao else None,
            "requestId": request.yeu_cau_du_doan_id,
            "requestCode": request.ma_yeu_cau,
            "predictionType": request.kieu_du_doan,
            "inputDrugName": thuoc.ten_thuoc if thuoc else None,
            "inputDiseaseName": benh.ten_benh if benh else None,
            "requestStatus": request.trang_thai_yeu_cau,
            "createdAt": request.ngay_tao.isoformat() if request.ngay_tao else None,
            "resultCount": count,
        })
    return out


def admin_history(db: Session, user_id: int | None, status: str | None) -> list[dict]:
    stmt = (
        select(YeuCauDuDoan, Thuoc, Benh, User)
        .outerjoin(Thuoc, YeuCauDuDoan.thuoc_dau_vao_id == Thuoc.thuoc_id)
        .outerjoin(Benh, YeuCauDuDoan.benh_dau_vao_id == Benh.benh_id)
        .outerjoin(User, YeuCauDuDoan.nguoi_dung_id == User.user_id)
    )
    if user_id:
        stmt = stmt.where(YeuCauDuDoan.nguoi_dung_id == user_id)
    if status:
        stmt = stmt.where(YeuCauDuDoan.trang_thai_yeu_cau == status.strip())
    rows = db.execute(stmt.order_by(YeuCauDuDoan.ngay_tao.desc()).limit(300)).all()
    out = []
    for request, thuoc, benh, requester in rows:
        count = db.execute(select(func.count(KetQuaDuDoan.ket_qua_du_doan_id)).where(KetQuaDuDoan.yeu_cau_du_doan_id == request.yeu_cau_du_doan_id)).scalar_one()
        out.append({
            "requestId": request.yeu_cau_du_doan_id,
            "requestCode": request.ma_yeu_cau,
            "requesterId": request.nguoi_dung_id,
            "requesterName": requester.full_name if requester else None,
            "requesterEmail": requester.email if requester else None,
            "predictionType": request.kieu_du_doan,
            "inputDrugId": request.thuoc_dau_vao_id,
            "inputDrugName": thuoc.ten_thuoc if thuoc else None,
            "inputDiseaseId": request.benh_dau_vao_id,
            "inputDiseaseName": benh.ten_benh if benh else None,
            "contactEmail": request.email_lien_he,
            "purpose": request.muc_dich,
            "requestStatus": request.trang_thai_yeu_cau,
            "createdAt": request.ngay_tao.isoformat() if request.ngay_tao else None,
            "resultCount": count,
        })
    return out
