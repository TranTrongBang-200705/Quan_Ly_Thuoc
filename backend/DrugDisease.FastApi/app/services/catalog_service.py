from __future__ import annotations

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.db_models import (
    Benh,
    LienKetThuocBenh,
    LoaiLienKet,
    MucTinCay,
    NguonDuLieu,
    NhomBenh,
    NhomThuoc,
    Thuoc,
    TrangThaiKiemDuyet,
)
from app.utils.exceptions import NotFoundError


MEDICAL_WARNING = "Thông tin chỉ phục vụ học tập, nghiên cứu và tham khảo. Không dùng để tự chẩn đoán, kê đơn hoặc thay thế tư vấn của bác sĩ/dược sĩ."


def _page(page: int | None) -> int:
    return max(1, int(page or 1))


def _page_size(page_size: int | None) -> int:
    return max(1, min(int(page_size or 12), 20000))


def _charindex_any(keyword: str, columns: list) -> object:
    term = keyword.strip()
    return or_(*[func.charindex(term, column) > 0 for column in columns])


def _as_float(value) -> float | None:
    return float(value) if value is not None else None


def thuoc_to_dto(
    thuoc: Thuoc,
    nhom_thuoc: NhomThuoc | None = None,
    trang_thai: TrangThaiKiemDuyet | None = None,
    nguon: NguonDuLieu | None = None,
) -> dict:
    dto = {
        "thuocId": thuoc.thuoc_id,
        "maThuoc": thuoc.ma_thuoc,
        "tenThuoc": thuoc.ten_thuoc,
        "tenThuocGoc": thuoc.ten_thuoc_goc,
        "hoatChat": thuoc.hoat_chat,
        "dangBaoChe": thuoc.dang_bao_che,
        "trangThaiPheDuyet": thuoc.trang_thai_phe_duyet,
        "congDung": thuoc.cong_dung,
        "tacDungPhu": thuoc.tac_dung_phu,
        "duongDanAnh": thuoc.duong_dan_anh,
        "nhaSanXuat": thuoc.nha_san_xuat,
        "tyLeDanhGiaTot": thuoc.ty_le_danh_gia_tot,
        "tyLeDanhGiaTrungBinh": thuoc.ty_le_danh_gia_trung_binh,
        "tyLeDanhGiaKem": thuoc.ty_le_danh_gia_kem,
        "tenNhomThuoc": nhom_thuoc.ten_nhom_thuoc if nhom_thuoc else None,
        "tenTrangThaiKiemDuyet": trang_thai.ten_trang_thai if trang_thai else None,
        "tenNguonDuLieu": nguon.ten_nguon if nguon else None,
        "canhBaoYTe": MEDICAL_WARNING,
        "drugId": thuoc.thuoc_id,
        "drugCode": thuoc.ma_thuoc,
        "activeName": thuoc.ten_thuoc,
        "tradeName": thuoc.ten_thuoc_goc or thuoc.hoat_chat,
        "knownIndications": thuoc.cong_dung,
    }
    if thuoc.co_che_tac_dong:
        dto["coCheTacDong"] = thuoc.co_che_tac_dong
    if thuoc.target_gene:
        dto["targetGene"] = thuoc.target_gene
    return dto


def benh_to_dto(
    benh: Benh,
    nhom_benh: NhomBenh | None = None,
    trang_thai: TrangThaiKiemDuyet | None = None,
    nguon: NguonDuLieu | None = None,
) -> dict:
    return {
        "benhId": benh.benh_id,
        "maBenh": benh.ma_benh,
        "tenBenh": benh.ten_benh,
        "tenDongNghia": benh.ten_dong_nghia,
        "moTa": benh.mo_ta,
        "trieuChung": benh.trieu_chung,
        "thuocDieuTriDaBiet": benh.thuoc_dieu_tri_da_biet,
        "tenNhomBenh": nhom_benh.ten_nhom_benh if nhom_benh else None,
        "tenTrangThaiKiemDuyet": trang_thai.ten_trang_thai if trang_thai else None,
        "tenNguonDuLieu": nguon.ten_nguon if nguon else None,
        "canhBaoYTe": MEDICAL_WARNING,
        "diseaseId": benh.benh_id,
        "diseaseCode": benh.ma_benh,
        "diseaseName": benh.ten_benh,
        "description": benh.mo_ta,
    }


def lien_ket_to_dto(
    link: LienKetThuocBenh,
    thuoc: Thuoc,
    benh: Benh,
    loai: LoaiLienKet | None,
    muc: MucTinCay | None,
    trang_thai: TrangThaiKiemDuyet | None = None,
) -> dict:
    return {
        "lienKetId": link.lien_ket_id,
        "thuocId": link.thuoc_id,
        "tenThuoc": thuoc.ten_thuoc,
        "benhId": link.benh_id,
        "tenBenh": benh.ten_benh,
        "loaiLienKetId": link.loai_lien_ket_id,
        "tenLoaiLienKet": loai.ten_loai_lien_ket if loai else None,
        "mucTinCayId": link.muc_tin_cay_id,
        "tenMucTinCay": muc.ten_muc_tin_cay if muc else None,
        "diemLienKet": _as_float(link.diem_lien_ket),
        "ghiChu": link.ghi_chu,
        "nguonBangChung": link.nguon_bang_chung,
        "maThamChieu": link.ma_tham_chieu,
        "tenTrangThaiKiemDuyet": trang_thai.ten_trang_thai if trang_thai else None,
        "linkId": link.lien_ket_id,
        "drugId": link.thuoc_id,
        "drugName": thuoc.ten_thuoc,
        "diseaseId": link.benh_id,
        "diseaseName": benh.ten_benh,
        "sourceScore": _as_float(link.diem_lien_ket),
        "confidenceLevel": muc.ten_muc_tin_cay if muc else None,
        "linkType": loai.ten_loai_lien_ket if loai else None,
        "evidenceDescription": link.ghi_chu or link.nguon_bang_chung,
    }


def list_thuoc(
    db: Session,
    tu_khoa: str | None = None,
    page: int | None = 1,
    page_size: int | None = 12,
    sap_xep: str | None = None,
    nha_san_xuat: str | None = None,
    nhom_thuoc_id: int | None = None,
) -> dict:
    stmt = (
        select(Thuoc, NhomThuoc, TrangThaiKiemDuyet, NguonDuLieu)
        .outerjoin(NhomThuoc, Thuoc.nhom_thuoc_id == NhomThuoc.nhom_thuoc_id)
        .outerjoin(TrangThaiKiemDuyet, Thuoc.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
        .outerjoin(NguonDuLieu, Thuoc.nguon_du_lieu_id == NguonDuLieu.nguon_du_lieu_id)
    )
    count_stmt = select(func.count(Thuoc.thuoc_id))

    filters = []
    if tu_khoa and tu_khoa.strip():
        filters.append(_charindex_any(tu_khoa, [Thuoc.ten_thuoc, Thuoc.hoat_chat, Thuoc.cong_dung, Thuoc.tac_dung_phu, Thuoc.nha_san_xuat]))
    if nha_san_xuat and nha_san_xuat.strip():
        filters.append(func.charindex(nha_san_xuat.strip(), Thuoc.nha_san_xuat) > 0)
    if nhom_thuoc_id:
        filters.append(Thuoc.nhom_thuoc_id == nhom_thuoc_id)
    for condition in filters:
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)

    sort_map = {
        "ten": Thuoc.ten_thuoc.asc(),
        "ten_desc": Thuoc.ten_thuoc.desc(),
        "danh_gia_tot": Thuoc.ty_le_danh_gia_tot.desc(),
        "moi_nhat": Thuoc.ngay_tao.desc(),
    }
    stmt = stmt.order_by(sort_map.get((sap_xep or "ten").strip(), Thuoc.ten_thuoc.asc()))

    current_page = _page(page)
    size = _page_size(page_size)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.offset((current_page - 1) * size).limit(size)).all()
    items = [thuoc_to_dto(*row) for row in rows]
    return {"items": items, "data": items, "total": total, "page": current_page, "pageSize": size}


def get_thuoc_detail(db: Session, thuoc_id: int) -> dict:
    row = db.execute(
        select(Thuoc, NhomThuoc, TrangThaiKiemDuyet, NguonDuLieu)
        .outerjoin(NhomThuoc, Thuoc.nhom_thuoc_id == NhomThuoc.nhom_thuoc_id)
        .outerjoin(TrangThaiKiemDuyet, Thuoc.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
        .outerjoin(NguonDuLieu, Thuoc.nguon_du_lieu_id == NguonDuLieu.nguon_du_lieu_id)
        .where(Thuoc.thuoc_id == thuoc_id)
    ).first()
    if row is None:
        raise NotFoundError("Không tìm thấy thuốc.")
    dto = thuoc_to_dto(*row)
    dto["benhLienQuan"] = search_links(db, thuoc_id=thuoc_id)
    return dto


def list_benh(db: Session, tu_khoa: str | None = None, page: int | None = 1, page_size: int | None = 12) -> dict:
    stmt = (
        select(Benh, NhomBenh, TrangThaiKiemDuyet, NguonDuLieu)
        .outerjoin(NhomBenh, Benh.nhom_benh_id == NhomBenh.nhom_benh_id)
        .outerjoin(TrangThaiKiemDuyet, Benh.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
        .outerjoin(NguonDuLieu, Benh.nguon_du_lieu_id == NguonDuLieu.nguon_du_lieu_id)
    )
    count_stmt = select(func.count(Benh.benh_id))
    if tu_khoa and tu_khoa.strip():
        condition = _charindex_any(tu_khoa, [Benh.ten_benh, Benh.ten_dong_nghia, Benh.mo_ta, Benh.trieu_chung, Benh.thuoc_dieu_tri_da_biet])
        stmt = stmt.where(condition)
        count_stmt = count_stmt.where(condition)
    current_page = _page(page)
    size = _page_size(page_size)
    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(stmt.order_by(Benh.ten_benh).offset((current_page - 1) * size).limit(size)).all()
    items = [benh_to_dto(*row) for row in rows]
    return {"items": items, "data": items, "total": total, "page": current_page, "pageSize": size}


def get_benh_detail(db: Session, benh_id: int) -> dict:
    row = db.execute(
        select(Benh, NhomBenh, TrangThaiKiemDuyet, NguonDuLieu)
        .outerjoin(NhomBenh, Benh.nhom_benh_id == NhomBenh.nhom_benh_id)
        .outerjoin(TrangThaiKiemDuyet, Benh.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
        .outerjoin(NguonDuLieu, Benh.nguon_du_lieu_id == NguonDuLieu.nguon_du_lieu_id)
        .where(Benh.benh_id == benh_id)
    ).first()
    if row is None:
        raise NotFoundError("Không tìm thấy bệnh.")
    dto = benh_to_dto(*row)
    dto["thuocLienQuan"] = search_links(db, benh_id=benh_id)
    return dto


def search_links(db: Session, thuoc_id: int | None = None, benh_id: int | None = None) -> list[dict]:
    stmt = (
        select(LienKetThuocBenh, Thuoc, Benh, LoaiLienKet, MucTinCay, TrangThaiKiemDuyet)
        .join(Thuoc, LienKetThuocBenh.thuoc_id == Thuoc.thuoc_id)
        .join(Benh, LienKetThuocBenh.benh_id == Benh.benh_id)
        .outerjoin(LoaiLienKet, LienKetThuocBenh.loai_lien_ket_id == LoaiLienKet.loai_lien_ket_id)
        .outerjoin(MucTinCay, LienKetThuocBenh.muc_tin_cay_id == MucTinCay.muc_tin_cay_id)
        .outerjoin(TrangThaiKiemDuyet, LienKetThuocBenh.trang_thai_kiem_duyet_id == TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)
    )
    if thuoc_id:
        stmt = stmt.where(LienKetThuocBenh.thuoc_id == thuoc_id)
    if benh_id:
        stmt = stmt.where(LienKetThuocBenh.benh_id == benh_id)
    rows = db.execute(stmt.order_by(LienKetThuocBenh.diem_lien_ket.desc()).limit(100)).all()
    return [lien_ket_to_dto(*row) for row in rows]


def get_lookups(db: Session) -> dict:
    def item(id_: int, code: str, name: str) -> dict:
        return {"id": id_, "code": code, "name": name}

    muc_tin_cay = db.execute(select(MucTinCay).order_by(MucTinCay.muc_tin_cay_id)).scalars().all()
    loai_lien_ket = db.execute(select(LoaiLienKet).order_by(LoaiLienKet.loai_lien_ket_id)).scalars().all()
    trang_thai = db.execute(select(TrangThaiKiemDuyet).order_by(TrangThaiKiemDuyet.trang_thai_kiem_duyet_id)).scalars().all()
    nhom_thuoc = db.execute(select(NhomThuoc).order_by(NhomThuoc.ten_nhom_thuoc)).scalars().all()
    nhom_benh = db.execute(select(NhomBenh).order_by(NhomBenh.ten_nhom_benh)).scalars().all()
    return {
        "predictionTypes": [
            item(1, "DRUG_TO_DISEASE", "Từ thuốc tìm bệnh"),
            item(2, "DISEASE_TO_DRUG", "Từ bệnh tìm thuốc"),
            item(3, "PAIR_PREDICTION", "Kiểm tra một cặp thuốc - bệnh"),
        ],
        "confidenceLevels": [item(x.muc_tin_cay_id, x.ma_muc_tin_cay, x.ten_muc_tin_cay) for x in muc_tin_cay],
        "linkTypes": [item(x.loai_lien_ket_id, x.ma_loai_lien_ket, x.ten_loai_lien_ket) for x in loai_lien_ket],
        "evidenceStatuses": [item(x.trang_thai_kiem_duyet_id, x.ma_trang_thai, x.ten_trang_thai) for x in trang_thai],
        "nhomThuoc": [item(x.nhom_thuoc_id, x.ma_nhom_thuoc, x.ten_nhom_thuoc) for x in nhom_thuoc],
        "nhomBenh": [item(x.nhom_benh_id, x.ma_nhom_benh, x.ten_nhom_benh) for x in nhom_benh],
    }


def search_drugs(db: Session, keyword: str | None, take: int) -> list[dict]:
    return list_thuoc(db, tu_khoa=keyword, page=1, page_size=take)["items"]


def search_diseases(db: Session, keyword: str | None, take: int) -> list[dict]:
    return list_benh(db, tu_khoa=keyword, page=1, page_size=take)["items"]
