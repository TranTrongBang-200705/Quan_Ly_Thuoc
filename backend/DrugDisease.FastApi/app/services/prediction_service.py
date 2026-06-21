from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select
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
from app.utils.exceptions import AppError, NotFoundError

MEDICAL_WARNING = "Thông tin chỉ phục vụ học tập, nghiên cứu và tham khảo. Không dùng để tự chẩn đoán, kê đơn hoặc thay thế tư vấn của bác sĩ/dược sĩ."


def code(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:24].upper()}"


def fmt(score: float) -> str:
    return f"{score:.5f}".rstrip("0").rstrip(".")


def normalize_prediction_type(value: str) -> str:
    raw = (value or "").strip().upper()
    mapping = {
        "DRUG_TO_DISEASE": "DRUG_TO_DISEASE",
        "THUOC_TIM_BENH": "DRUG_TO_DISEASE",
        "TU_THUOC_TIM_BENH": "DRUG_TO_DISEASE",
        "DISEASE_TO_DRUG": "DISEASE_TO_DRUG",
        "BENH_TIM_THUOC": "DISEASE_TO_DRUG",
        "TU_BENH_TIM_THUOC": "DISEASE_TO_DRUG",
        "PAIR_PREDICTION": "PAIR_PREDICTION",
        "KIEM_TRA_CAP": "PAIR_PREDICTION",
        "KIEM_TRA_CAP_THUOC_BENH": "PAIR_PREDICTION",
    }
    if raw not in mapping:
        raise AppError("Kiểu dự đoán chỉ nhận DRUG_TO_DISEASE, DISEASE_TO_DRUG hoặc PAIR_PREDICTION.")
    return mapping[raw]


def validate_request(req: PredictionCreateRequest) -> str:
    prediction_type = normalize_prediction_type(req.prediction_type)
    if not req.contact_email:
        raise AppError("Vui lòng nhập email liên hệ.")
    if not req.medical_warning_accepted:
        raise AppError("Vui lòng xác nhận cảnh báo y tế trước khi dự đoán.")
    if prediction_type == "DRUG_TO_DISEASE" and req.drug_id is None:
        raise AppError("Từ thuốc tìm bệnh cần nhập ThuocId.")
    if prediction_type == "DISEASE_TO_DRUG" and req.disease_id is None:
        raise AppError("Từ bệnh tìm thuốc cần nhập BenhId.")
    if prediction_type == "PAIR_PREDICTION" and (req.drug_id is None or req.disease_id is None):
        raise AppError("Kiểm tra một cặp thuốc - bệnh cần nhập cả ThuocId và BenhId.")
    return prediction_type


def get_thuoc_or_throw(db: Session, thuoc_id: int | None) -> Thuoc:
    if thuoc_id is None:
        raise AppError("Vui lòng nhập ThuocId.")
    thuoc = db.execute(select(Thuoc).where(Thuoc.thuoc_id == thuoc_id)).scalar_one_or_none()
    if thuoc is None:
        max_id = db.execute(select(func.max(Thuoc.thuoc_id))).scalar_one_or_none()
        raise AppError(f"ThuocId={thuoc_id} không tồn tại. ThuocId lớn nhất hiện có là {max_id or 0}.")
    return thuoc


def get_benh_or_throw(db: Session, benh_id: int | None) -> Benh:
    if benh_id is None:
        raise AppError("Vui lòng nhập BenhId.")
    benh = db.execute(select(Benh).where(Benh.benh_id == benh_id)).scalar_one_or_none()
    if benh is None:
        max_id = db.execute(select(func.max(Benh.benh_id))).scalar_one_or_none()
        raise AppError(f"BenhId={benh_id} không tồn tại. BenhId lớn nhất hiện có là {max_id or 0}.")
    return benh


def confidence_id(score: float, levels: list[MucTinCay]) -> int | None:
    for level in levels:
        min_score = float(level.diem_tu) if level.diem_tu is not None else None
        max_score = float(level.diem_den) if level.diem_den is not None else None
        if (min_score is None or score >= min_score) and (max_score is None or score <= max_score):
            return level.muc_tin_cay_id
    return None


def candidate_rows(db: Session, req: PredictionCreateRequest, prediction_type: str) -> list:
    stmt = (
        select(LienKetThuocBenh, Thuoc, Benh, LoaiLienKet, MucTinCay)
        .join(Thuoc, LienKetThuocBenh.thuoc_id == Thuoc.thuoc_id)
        .join(Benh, LienKetThuocBenh.benh_id == Benh.benh_id)
        .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
    )
    if prediction_type == "DRUG_TO_DISEASE":
        get_thuoc_or_throw(db, req.drug_id)
        stmt = stmt.where(LienKetThuocBenh.thuoc_id == req.drug_id)
    elif prediction_type == "DISEASE_TO_DRUG":
        get_benh_or_throw(db, req.disease_id)
        stmt = stmt.where(LienKetThuocBenh.benh_id == req.disease_id)
    else:
        get_thuoc_or_throw(db, req.drug_id)
        get_benh_or_throw(db, req.disease_id)
        stmt = stmt.where(LienKetThuocBenh.thuoc_id == req.drug_id, LienKetThuocBenh.benh_id == req.disease_id)
    return db.execute(stmt.order_by(LienKetThuocBenh.diem_lien_ket.desc())).all()


def result_dto(result: KetQuaDuDoan, thuoc: Thuoc, benh: Benh, muc: MucTinCay | None, loai: LoaiLienKet | None) -> dict:
    score = float(result.diem_du_doan)
    return {
        "ketQuaDuDoanId": result.ket_qua_du_doan_id,
        "yeuCauDuDoanId": result.yeu_cau_du_doan_id,
        "thuHang": result.thu_hang,
        "thuocId": result.thuoc_id,
        "tenThuoc": thuoc.ten_thuoc,
        "benhId": result.benh_id,
        "tenBenh": benh.ten_benh,
        "diemDuDoan": score,
        "tenMucTinCay": muc.ten_muc_tin_cay if muc else None,
        "tenLoaiLienKet": loai.ten_loai_lien_ket if loai else None,
        "giaiThichNgan": result.giai_thich_ngan,
        "canhBaoYTe": result.canh_bao_y_te or MEDICAL_WARNING,
        "predictionResultId": result.ket_qua_du_doan_id,
        "rankNo": result.thu_hang,
        "drugId": result.thuoc_id,
        "drugName": thuoc.ten_thuoc,
        "diseaseId": result.benh_id,
        "diseaseName": benh.ten_benh,
        "predictionScore": score,
        "confidenceLevel": muc.ten_muc_tin_cay if muc else None,
        "linkType": loai.ten_loai_lien_ket if loai else None,
        "explanationText": result.giai_thich_ngan,
        "warningText": result.canh_bao_y_te or MEDICAL_WARNING,
    }


async def create_prediction(db: Session, req: PredictionCreateRequest, user: User) -> dict:
    prediction_type = validate_request(req)
    threshold = float(req.score_threshold or 0)
    top_k = max(1, min(int(req.top_k or 10), 100))
    rows = candidate_rows(db, req, prediction_type)
    levels = db.execute(select(MucTinCay).order_by(MucTinCay.diem_tu.desc())).scalars().all()
    model = db.execute(select(MoHinhMayHoc).where(MoHinhMayHoc.dang_duoc_dung.is_(True))).scalar_one_or_none()

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
        trang_thai_yeu_cau="Đang xử lý",
        ngay_tao=datetime.utcnow(),
    )
    db.add(request)
    db.flush()

    selected = []
    for link, thuoc, benh, loai, muc in rows:
        score = float(link.diem_lien_ket or 0)
        if score >= threshold:
            selected.append((link, thuoc, benh, loai, muc, score))
        if len(selected) >= top_k:
            break

    for rank, (link, thuoc, benh, loai, muc, score) in enumerate(selected, start=1):
        db.add(
            KetQuaDuDoan(
                yeu_cau_du_doan_id=request.yeu_cau_du_doan_id,
                thuoc_id=thuoc.thuoc_id,
                benh_id=benh.benh_id,
                thu_hang=rank,
                diem_du_doan=score,
                muc_tin_cay_id=muc.muc_tin_cay_id if muc else confidence_id(score, levels),
                loai_lien_ket_id=loai.loai_lien_ket_id if loai else link.loai_lien_ket_id,
                giai_thich_ngan=link.ghi_chu or f"Kết quả tạm thời dựa trên liên kết đã có trong DataThuoc. Mô hình: {model.ten_mo_hinh if model else 'rule-based fallback'}.",
                canh_bao_y_te=MEDICAL_WARNING,
                ngay_tao=datetime.utcnow(),
            )
        )
    request.trang_thai_yeu_cau = "Hoàn thành"
    db.commit()
    return get_prediction(db, request.yeu_cau_du_doan_id) or {}


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
    return {
        "yeuCauDuDoanId": request.yeu_cau_du_doan_id,
        "maYeuCau": request.ma_yeu_cau,
        "kieuDuDoan": request.kieu_du_doan,
        "trangThaiYeuCau": request.trang_thai_yeu_cau,
        "ngayTao": request.ngay_tao.isoformat() if request.ngay_tao else None,
        "nguongDiem": float(request.nguong_diem or 0),
        "resultMessage": f"Tìm thấy {len(results)} kết quả phù hợp." if results else "Không có kết quả phù hợp với dữ liệu liên kết hiện có.",
        "results": results,
        "requestId": request.yeu_cau_du_doan_id,
        "requestCode": request.ma_yeu_cau,
        "predictionRunId": request.yeu_cau_du_doan_id,
        "runCode": request.ma_yeu_cau,
        "requestStatus": request.trang_thai_yeu_cau,
        "createdAt": request.ngay_tao.isoformat() if request.ngay_tao else None,
        "scoreThreshold": float(request.nguong_diem or 0),
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
