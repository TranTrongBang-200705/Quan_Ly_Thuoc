from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.db_models import Benh, LienKetThuocBenh, LoaiLienKet, MucTinCay, Thuoc, TrangThaiKiemDuyet, User
from app.schemas.dto import LinkCreateRequest, LinkUpdateRequest
from app.services.catalog_service import lien_ket_to_dto
from app.utils.exceptions import AppError, NotFoundError


def normalize(value: str | None) -> str | None:
    if value is None or not value.strip():
        return None
    return value.strip()


def _exists(db: Session, model, field, value: int, label: str) -> None:
    row = db.execute(select(model).where(field == value)).scalar_one_or_none()
    if row is None:
        raise NotFoundError(f"Không tìm thấy {label}={value}.")


def validate_references(db: Session, thuoc_id: int, benh_id: int, loai_lien_ket_id: int, trang_thai_id: int | None, muc_tin_cay_id: int | None) -> None:
    _exists(db, Thuoc, Thuoc.thuoc_id, thuoc_id, "ThuocId")
    _exists(db, Benh, Benh.benh_id, benh_id, "BenhId")
    _exists(db, LoaiLienKet, LoaiLienKet.loai_lien_ket_id, loai_lien_ket_id, "LoaiLienKetId")
    if trang_thai_id is not None:
        _exists(db, TrangThaiKiemDuyet, TrangThaiKiemDuyet.trang_thai_kiem_duyet_id, trang_thai_id, "TrangThaiKiemDuyetId")
    if muc_tin_cay_id is not None:
        _exists(db, MucTinCay, MucTinCay.muc_tin_cay_id, muc_tin_cay_id, "MucTinCayId")


def admin_search_links(db: Session, drug_id: int | None, disease_id: int | None) -> list[dict]:
    stmt = (
        select(LienKetThuocBenh, Thuoc, Benh, LoaiLienKet, MucTinCay, TrangThaiKiemDuyet)
        .join(Thuoc, LienKetThuocBenh.thuoc_id == Thuoc.thuoc_id)
        .join(Benh, LienKetThuocBenh.benh_id == Benh.benh_id)
        .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
        .outerjoin(TrangThaiKiemDuyet, LienKetThuocBenh.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
    )
    if drug_id:
        stmt = stmt.where(LienKetThuocBenh.thuoc_id == drug_id)
    if disease_id:
        stmt = stmt.where(LienKetThuocBenh.benh_id == disease_id)
    rows = db.execute(stmt.order_by(LienKetThuocBenh.ngay_tao.desc()).limit(300)).all()
    return [lien_ket_to_dto(link, thuoc, benh, loai, muc, trang_thai) for link, thuoc, benh, loai, muc, trang_thai in rows]


def get_admin_link_by_id(db: Session, link_id: int) -> dict:
    row = db.execute(
        select(LienKetThuocBenh, Thuoc, Benh, LoaiLienKet, MucTinCay, TrangThaiKiemDuyet)
        .join(Thuoc, LienKetThuocBenh.thuoc_id == Thuoc.thuoc_id)
        .join(Benh, LienKetThuocBenh.benh_id == Benh.benh_id)
        .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
        .outerjoin(TrangThaiKiemDuyet, LienKetThuocBenh.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
        .where(LienKetThuocBenh.lien_ket_id == link_id)
    ).first()
    if row is None:
        raise NotFoundError("Không tìm thấy liên kết thuốc - bệnh.")
    return lien_ket_to_dto(*row)


def create_link(db: Session, request: LinkCreateRequest, user: User) -> dict:
    validate_references(db, request.drug_id, request.disease_id, request.link_type_id, request.evidence_status_id, request.confidence_level_id)
    existing = db.execute(
        select(LienKetThuocBenh).where(
            LienKetThuocBenh.thuoc_id == request.drug_id,
            LienKetThuocBenh.benh_id == request.disease_id,
            LienKetThuocBenh.loai_lien_ket_id == request.link_type_id,
        )
    ).scalar_one_or_none()
    if existing:
        raise AppError("Liên kết thuốc - bệnh với loại liên kết này đã tồn tại.")
    link = LienKetThuocBenh(
        thuoc_id=request.drug_id,
        benh_id=request.disease_id,
        loai_lien_ket_id=request.link_type_id,
        trang_thai_kiem_duyet_id=request.evidence_status_id,
        muc_tin_cay_id=request.confidence_level_id,
        diem_lien_ket=request.source_score,
        nguon_bang_chung=normalize(request.formation_basis),
        ghi_chu=normalize(request.evidence_description),
    )
    db.add(link)
    db.commit()
    return get_admin_link_by_id(db, link.lien_ket_id)


def update_link(db: Session, link_id: int, request: LinkUpdateRequest, user: User) -> dict:
    link = db.execute(select(LienKetThuocBenh).where(LienKetThuocBenh.lien_ket_id == link_id)).scalar_one_or_none()
    if link is None:
        raise NotFoundError("Không tìm thấy liên kết thuốc - bệnh cần sửa.")
    validate_references(db, request.drug_id, request.disease_id, request.link_type_id, request.evidence_status_id, request.confidence_level_id)
    link.thuoc_id = request.drug_id
    link.benh_id = request.disease_id
    link.loai_lien_ket_id = request.link_type_id
    link.trang_thai_kiem_duyet_id = request.evidence_status_id
    link.muc_tin_cay_id = request.confidence_level_id
    link.diem_lien_ket = request.source_score
    link.nguon_bang_chung = normalize(request.formation_basis)
    link.ghi_chu = normalize(request.evidence_description)
    db.commit()
    return get_admin_link_by_id(db, link.lien_ket_id)


def delete_link(db: Session, link_id: int, user: User) -> None:
    raise AppError("Schema DataThuoc hiện chưa có cột xóa mềm cho LienKetThuocBenh; không xóa dữ liệu bằng API này.", 405)
