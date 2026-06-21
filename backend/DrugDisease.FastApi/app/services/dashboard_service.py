from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.db_models import Benh, KetQuaDuDoan, LienKetThuocBenh, PhanHoiKetQua, Thuoc, YeuCauDuDoan


def admin_dashboard(db: Session) -> dict:
    return {
        "totalDrugs": db.execute(select(func.count(Thuoc.thuoc_id))).scalar_one(),
        "totalDiseases": db.execute(select(func.count(Benh.benh_id))).scalar_one(),
        "totalLinks": db.execute(select(func.count(LienKetThuocBenh.lien_ket_id))).scalar_one(),
        "totalPredictionRequests": db.execute(select(func.count(YeuCauDuDoan.yeu_cau_du_doan_id))).scalar_one(),
        "totalPredictionResults": db.execute(select(func.count(KetQuaDuDoan.ket_qua_du_doan_id))).scalar_one(),
        "totalFeedbacks": db.execute(select(func.count(PhanHoiKetQua.phan_hoi_id))).scalar_one(),
    }
