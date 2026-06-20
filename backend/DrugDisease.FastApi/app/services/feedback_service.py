from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import KetQuaDuDoan, PhanHoiKetQua, User
from app.schemas.dto import FeedbackCreateRequest
from app.utils.exceptions import NotFoundError


def normalize_assessment(value: str) -> str:
    v = value.strip().lower()
    mapping = {
        "useful": "Hợp lý",
        "reasonable": "Hợp lý",
        "ok": "Hợp lý",
        "correct": "Hợp lý",
        "good": "Hợp lý",
        "hợp lý": "Hợp lý",
        "hop ly": "Hợp lý",
        "not_useful": "Chưa hợp lý",
        "incorrect": "Chưa hợp lý",
        "wrong": "Chưa hợp lý",
        "bad": "Chưa hợp lý",
        "chưa hợp lý": "Chưa hợp lý",
        "chua hop ly": "Chưa hợp lý",
        "need_check": "Cần kiểm chứng thêm",
        "need_review": "Cần kiểm chứng thêm",
        "review": "Cần kiểm chứng thêm",
        "unknown": "Không đủ thông tin để đánh giá",
        "not_enough_info": "Không đủ thông tin để đánh giá",
    }
    return mapping.get(v, value.strip() or "Cần kiểm chứng thêm")


def create_feedback(db: Session, request: FeedbackCreateRequest, user: User) -> dict:
    result_id = request.prediction_result_id or request.ket_qua_du_doan_id
    if result_id is None:
        raise NotFoundError("Vui lòng gửi KetQuaDuDoanId.")
    result = db.execute(select(KetQuaDuDoan).where(KetQuaDuDoan.ket_qua_du_doan_id == result_id)).scalar_one_or_none()
    if result is None:
        raise NotFoundError(f"Không tìm thấy KetQuaDuDoanId = {result_id}.")
    feedback = PhanHoiKetQua(
        ket_qua_du_doan_id=result_id,
        nguoi_dung_id=request.user_id or user.user_id,
        danh_gia=normalize_assessment(request.general_assessment or request.danh_gia or "Cần kiểm chứng thêm"),
        nhan_xet=request.reason_text.strip() if request.reason_text else request.nhan_xet,
        nguon_tham_khao_bo_sung=request.suggested_action.strip() if request.suggested_action else request.nguon_tham_khao_bo_sung,
        trang_thai_xu_ly="Chờ xử lý",
        ngay_tao=datetime.utcnow(),
    )
    db.add(feedback)
    db.commit()
    return {
        "phanHoiId": feedback.phan_hoi_id,
        "ketQuaDuDoanId": feedback.ket_qua_du_doan_id,
        "danhGia": feedback.danh_gia,
        "nhanXet": feedback.nhan_xet,
        "trangThaiXuLy": feedback.trang_thai_xu_ly,
        "ngayTao": feedback.ngay_tao.isoformat() if feedback.ngay_tao else None,
        "feedbackId": feedback.phan_hoi_id,
        "generalAssessment": feedback.danh_gia,
        "reasonText": feedback.nhan_xet,
        "createdAt": feedback.ngay_tao.isoformat() if feedback.ngay_tao else None,
    }
