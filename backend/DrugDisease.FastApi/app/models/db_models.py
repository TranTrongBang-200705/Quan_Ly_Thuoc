from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.core.database import Base


def now_utc() -> datetime:
    return datetime.utcnow()


class Role(Base):
    __tablename__ = "VaiTro"
    __table_args__ = {"implicit_returning": False}

    role_id: Mapped[int] = mapped_column("VaiTroId", Integer, primary_key=True, autoincrement=True)
    role_code: Mapped[str] = mapped_column("MaVaiTro", String(50), unique=True)
    role_name: Mapped[str] = mapped_column("TenVaiTro", String(100))
    description: Mapped[str | None] = mapped_column("MoTa", String(300))

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")


class User(Base):
    __tablename__ = "NguoiDung"
    __table_args__ = {"implicit_returning": False}

    user_id: Mapped[int] = mapped_column("NguoiDungId", Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column("HoTen", String(150))
    email: Mapped[str] = mapped_column("Email", String(200), unique=True)
    username: Mapped[str] = mapped_column("TenDangNhap", String(100), unique=True)
    password_hash: Mapped[str] = mapped_column("MatKhauBam", String(500))
    account_status: Mapped[str] = mapped_column("TrangThaiTaiKhoan", Unicode(50), default="Hoạt động")
    created_at: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)
    updated_at: Mapped[datetime | None] = mapped_column("NgayCapNhat", DateTime)

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user")


class UserRole(Base):
    __tablename__ = "NguoiDungVaiTro"
    __table_args__ = {"implicit_returning": False}

    user_id: Mapped[int] = mapped_column("NguoiDungId", ForeignKey("NguoiDung.NguoiDungId"), primary_key=True)
    role_id: Mapped[int] = mapped_column("VaiTroId", ForeignKey("VaiTro.VaiTroId"), primary_key=True)
    assigned_at: Mapped[datetime] = mapped_column("NgayGan", DateTime, default=now_utc)

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")


class UserSession(Base):
    __tablename__ = "NguoiDungPhienDangNhap"
    __table_args__ = {"implicit_returning": False}

    session_id: Mapped[int] = mapped_column("PhienDangNhapId", Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column("NguoiDungId", ForeignKey("NguoiDung.NguoiDungId"))
    session_code: Mapped[str] = mapped_column("MaPhien", String(200))
    ip_address: Mapped[str | None] = mapped_column("DiaChiIp", String(100))
    started_at: Mapped[datetime] = mapped_column("NgayBatDau", DateTime, default=now_utc)
    expires_at: Mapped[datetime | None] = mapped_column("NgayHetHan", DateTime)
    is_revoked: Mapped[bool] = mapped_column("DaThuHoi", Boolean, default=False)


class NguonDuLieu(Base):
    __tablename__ = "NguonDuLieu"
    __table_args__ = {"implicit_returning": False}

    nguon_du_lieu_id: Mapped[int] = mapped_column("NguonDuLieuId", Integer, primary_key=True, autoincrement=True)
    ma_nguon: Mapped[str] = mapped_column("MaNguon", String(80), unique=True)
    ten_nguon: Mapped[str] = mapped_column("TenNguon", String(200))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(500))


class TrangThaiKiemDuyet(Base):
    __tablename__ = "TrangThaiKiemDuyet"
    __table_args__ = {"implicit_returning": False}

    trang_thai_kiem_duyet_id: Mapped[int] = mapped_column("TrangThaiKiemDuyetId", Integer, primary_key=True, autoincrement=True)
    ma_trang_thai: Mapped[str] = mapped_column("MaTrangThai", String(80), unique=True)
    ten_trang_thai: Mapped[str] = mapped_column("TenTrangThai", String(150))


class MucTinCay(Base):
    __tablename__ = "MucTinCay"
    __table_args__ = {"implicit_returning": False}

    muc_tin_cay_id: Mapped[int] = mapped_column("MucTinCayId", Integer, primary_key=True, autoincrement=True)
    ma_muc_tin_cay: Mapped[str] = mapped_column("MaMucTinCay", String(80), unique=True)
    ten_muc_tin_cay: Mapped[str] = mapped_column("TenMucTinCay", String(150))
    diem_tu: Mapped[float | None] = mapped_column("DiemTu", Numeric(5, 4))
    diem_den: Mapped[float | None] = mapped_column("DiemDen", Numeric(5, 4))

    confidence_level_id = synonym("muc_tin_cay_id")
    level_code = synonym("ma_muc_tin_cay")
    level_name = synonym("ten_muc_tin_cay")
    min_score = synonym("diem_tu")
    max_score = synonym("diem_den")


class NhomThuoc(Base):
    __tablename__ = "NhomThuoc"
    __table_args__ = {"implicit_returning": False}

    nhom_thuoc_id: Mapped[int] = mapped_column("NhomThuocId", Integer, primary_key=True, autoincrement=True)
    ma_nhom_thuoc: Mapped[str] = mapped_column("MaNhomThuoc", String(80), unique=True)
    ten_nhom_thuoc: Mapped[str] = mapped_column("TenNhomThuoc", String(200))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(500))


class NhomBenh(Base):
    __tablename__ = "NhomBenh"
    __table_args__ = {"implicit_returning": False}

    nhom_benh_id: Mapped[int] = mapped_column("NhomBenhId", Integer, primary_key=True, autoincrement=True)
    ma_nhom_benh: Mapped[str] = mapped_column("MaNhomBenh", String(80), unique=True)
    ten_nhom_benh: Mapped[str] = mapped_column("TenNhomBenh", String(200))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(500))


class LoaiLienKet(Base):
    __tablename__ = "LoaiLienKet"
    __table_args__ = {"implicit_returning": False}

    loai_lien_ket_id: Mapped[int] = mapped_column("LoaiLienKetId", Integer, primary_key=True, autoincrement=True)
    ma_loai_lien_ket: Mapped[str] = mapped_column("MaLoaiLienKet", String(80), unique=True)
    ten_loai_lien_ket: Mapped[str] = mapped_column("TenLoaiLienKet", String(200))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(500))

    link_type_id = synonym("loai_lien_ket_id")
    link_type_code = synonym("ma_loai_lien_ket")
    link_type_name = synonym("ten_loai_lien_ket")


class Thuoc(Base):
    __tablename__ = "Thuoc"
    __table_args__ = {"implicit_returning": False}

    thuoc_id: Mapped[int] = mapped_column("ThuocId", Integer, primary_key=True, autoincrement=True)
    ma_thuoc: Mapped[str] = mapped_column("MaThuoc", String(40), unique=True)
    ten_thuoc: Mapped[str] = mapped_column("TenThuoc", String(250))
    ten_thuoc_goc: Mapped[str | None] = mapped_column("TenThuocGoc", String(250))
    hoat_chat: Mapped[str | None] = mapped_column("HoatChat", String(500))
    nhom_thuoc_id: Mapped[int | None] = mapped_column("NhomThuocId", ForeignKey("NhomThuoc.NhomThuocId"))
    co_che_tac_dong: Mapped[str | None] = mapped_column("CoCheTacDong", String(1000))
    target_gene: Mapped[str | None] = mapped_column("TargetGene", String(1000))
    dang_bao_che: Mapped[str | None] = mapped_column("DangBaoChe", String(150))
    trang_thai_phe_duyet: Mapped[str | None] = mapped_column("TrangThaiPheDuyet", String(150))
    cong_dung: Mapped[str | None] = mapped_column("CongDung", String(1000))
    tac_dung_phu: Mapped[str | None] = mapped_column("TacDungPhu", String(1000))
    duong_dan_anh: Mapped[str | None] = mapped_column("DuongDanAnh", String(1000))
    nha_san_xuat: Mapped[str | None] = mapped_column("NhaSanXuat", String(300))
    ty_le_danh_gia_tot: Mapped[int | None] = mapped_column("TyLeDanhGiaTot", Integer)
    ty_le_danh_gia_trung_binh: Mapped[int | None] = mapped_column("TyLeDanhGiaTrungBinh", Integer)
    ty_le_danh_gia_kem: Mapped[int | None] = mapped_column("TyLeDanhGiaKem", Integer)
    nguon_du_lieu_id: Mapped[int | None] = mapped_column("NguonDuLieuId", ForeignKey("NguonDuLieu.NguonDuLieuId"))
    trang_thai_kiem_duyet_id: Mapped[int | None] = mapped_column("TrangThaiKiemDuyetId", ForeignKey("TrangThaiKiemDuyet.TrangThaiKiemDuyetId"))
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)
    ngay_cap_nhat: Mapped[datetime | None] = mapped_column("NgayCapNhat", DateTime)

    nhom_thuoc: Mapped[NhomThuoc | None] = relationship()
    nguon_du_lieu: Mapped[NguonDuLieu | None] = relationship()
    trang_thai_kiem_duyet: Mapped[TrangThaiKiemDuyet | None] = relationship()

    drug_id = synonym("thuoc_id")
    drug_code = synonym("ma_thuoc")
    active_name = synonym("ten_thuoc")
    trade_name = synonym("ten_thuoc_goc")
    drug_group_id = synonym("nhom_thuoc_id")
    dosage_form_strength = synonym("dang_bao_che")
    known_indications = synonym("cong_dung")
    side_effects_warnings = synonym("tac_dung_phu")
    created_at = synonym("ngay_tao")
    updated_at = synonym("ngay_cap_nhat")


class Benh(Base):
    __tablename__ = "Benh"
    __table_args__ = {"implicit_returning": False}

    benh_id: Mapped[int] = mapped_column("BenhId", Integer, primary_key=True, autoincrement=True)
    ma_benh: Mapped[str] = mapped_column("MaBenh", String(40), unique=True)
    ten_benh: Mapped[str] = mapped_column("TenBenh", String(500))
    ten_dong_nghia: Mapped[str | None] = mapped_column("TenDongNghia", String(1000))
    nhom_benh_id: Mapped[int | None] = mapped_column("NhomBenhId", ForeignKey("NhomBenh.NhomBenhId"))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(2000))
    trieu_chung: Mapped[str | None] = mapped_column("TrieuChung", String(2000))
    gene_pathway_lien_quan: Mapped[str | None] = mapped_column("GenePathwayLienQuan", String(1000))
    thuoc_dieu_tri_da_biet: Mapped[str | None] = mapped_column("ThuocDieuTriDaBiet", String(2000))
    nguon_du_lieu_id: Mapped[int | None] = mapped_column("NguonDuLieuId", ForeignKey("NguonDuLieu.NguonDuLieuId"))
    trang_thai_kiem_duyet_id: Mapped[int | None] = mapped_column("TrangThaiKiemDuyetId", ForeignKey("TrangThaiKiemDuyet.TrangThaiKiemDuyetId"))
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)
    ngay_cap_nhat: Mapped[datetime | None] = mapped_column("NgayCapNhat", DateTime)

    nhom_benh: Mapped[NhomBenh | None] = relationship()
    nguon_du_lieu: Mapped[NguonDuLieu | None] = relationship()
    trang_thai_kiem_duyet: Mapped[TrangThaiKiemDuyet | None] = relationship()

    disease_id = synonym("benh_id")
    disease_code = synonym("ma_benh")
    disease_name = synonym("ten_benh")
    description = synonym("mo_ta")
    symptoms = synonym("trieu_chung")
    known_treatments = synonym("thuoc_dieu_tri_da_biet")
    disease_group_id = synonym("nhom_benh_id")


class LienKetThuocBenh(Base):
    __tablename__ = "LienKetThuocBenh"
    __table_args__ = {"implicit_returning": False}

    lien_ket_id: Mapped[int] = mapped_column("LienKetId", Integer, primary_key=True, autoincrement=True)
    thuoc_id: Mapped[int] = mapped_column("ThuocId", ForeignKey("Thuoc.ThuocId"))
    benh_id: Mapped[int] = mapped_column("BenhId", ForeignKey("Benh.BenhId"))
    loai_lien_ket_id: Mapped[int] = mapped_column("LoaiLienKetId", ForeignKey("LoaiLienKet.LoaiLienKetId"))
    nguon_bang_chung: Mapped[str | None] = mapped_column("NguonBangChung", String(500))
    ma_tham_chieu: Mapped[str | None] = mapped_column("MaThamChieu", String(200))
    trang_thai_kiem_duyet_id: Mapped[int | None] = mapped_column("TrangThaiKiemDuyetId", ForeignKey("TrangThaiKiemDuyet.TrangThaiKiemDuyetId"))
    muc_tin_cay_id: Mapped[int | None] = mapped_column("MucTinCayId", ForeignKey("MucTinCay.MucTinCayId"))
    diem_lien_ket: Mapped[float | None] = mapped_column("DiemLienKet", Numeric(6, 5))
    ghi_chu: Mapped[str | None] = mapped_column("GhiChu", String(1000))
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)

    thuoc: Mapped[Thuoc] = relationship()
    benh: Mapped[Benh] = relationship()
    loai_lien_ket: Mapped[LoaiLienKet] = relationship()
    muc_tin_cay: Mapped[MucTinCay | None] = relationship()
    trang_thai_kiem_duyet: Mapped[TrangThaiKiemDuyet | None] = relationship()

    link_id = synonym("lien_ket_id")
    drug_id = synonym("thuoc_id")
    disease_id = synonym("benh_id")
    link_type_id = synonym("loai_lien_ket_id")
    confidence_level_id = synonym("muc_tin_cay_id")
    source_score = synonym("diem_lien_ket")
    evidence_description = synonym("ghi_chu")
    created_at = synonym("ngay_tao")


class YeuCauDuDoan(Base):
    __tablename__ = "YeuCauDuDoan"
    __table_args__ = {"implicit_returning": False}

    yeu_cau_du_doan_id: Mapped[int] = mapped_column("YeuCauDuDoanId", Integer, primary_key=True, autoincrement=True)
    ma_yeu_cau: Mapped[str] = mapped_column("MaYeuCau", String(50), unique=True)
    nguoi_dung_id: Mapped[int | None] = mapped_column("NguoiDungId", ForeignKey("NguoiDung.NguoiDungId"))
    kieu_du_doan: Mapped[str] = mapped_column("KieuDuDoan", String(80))
    thuoc_dau_vao_id: Mapped[int | None] = mapped_column("ThuocDauVaoId", ForeignKey("Thuoc.ThuocId"))
    benh_dau_vao_id: Mapped[int | None] = mapped_column("BenhDauVaoId", ForeignKey("Benh.BenhId"))
    so_luong_ket_qua: Mapped[int] = mapped_column("SoLuongKetQua", Integer, default=10)
    nguong_diem: Mapped[float | None] = mapped_column("NguongDiem", Numeric(6, 5))
    muc_dich: Mapped[str | None] = mapped_column("MucDich", String(500))
    email_lien_he: Mapped[str | None] = mapped_column("EmailLienHe", String(200))
    da_chap_nhan_canh_bao_y_te: Mapped[bool] = mapped_column("DaChapNhanCanhBaoYTe", Boolean, default=False)
    trang_thai_yeu_cau: Mapped[str] = mapped_column("TrangThaiYeuCau", String(80), default="Đã gửi")
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)

    nguoi_dung: Mapped[User | None] = relationship()
    thuoc_dau_vao: Mapped[Thuoc | None] = relationship(foreign_keys=[thuoc_dau_vao_id])
    benh_dau_vao: Mapped[Benh | None] = relationship(foreign_keys=[benh_dau_vao_id])


class KetQuaDuDoan(Base):
    __tablename__ = "KetQuaDuDoan"
    __table_args__ = {"implicit_returning": False}

    ket_qua_du_doan_id: Mapped[int] = mapped_column("KetQuaDuDoanId", Integer, primary_key=True, autoincrement=True)
    yeu_cau_du_doan_id: Mapped[int] = mapped_column("YeuCauDuDoanId", ForeignKey("YeuCauDuDoan.YeuCauDuDoanId"))
    thuoc_id: Mapped[int] = mapped_column("ThuocId", ForeignKey("Thuoc.ThuocId"))
    benh_id: Mapped[int] = mapped_column("BenhId", ForeignKey("Benh.BenhId"))
    thu_hang: Mapped[int] = mapped_column("ThuHang", Integer)
    diem_du_doan: Mapped[float] = mapped_column("DiemDuDoan", Numeric(6, 5))
    muc_tin_cay_id: Mapped[int | None] = mapped_column("MucTinCayId", ForeignKey("MucTinCay.MucTinCayId"))
    loai_lien_ket_id: Mapped[int | None] = mapped_column("LoaiLienKetId", ForeignKey("LoaiLienKet.LoaiLienKetId"))
    giai_thich_ngan: Mapped[str | None] = mapped_column("GiaiThichNgan", String(1000))
    canh_bao_y_te: Mapped[str | None] = mapped_column("CanhBaoYTe", String(1000))
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)

    yeu_cau: Mapped[YeuCauDuDoan] = relationship()
    thuoc: Mapped[Thuoc] = relationship()
    benh: Mapped[Benh] = relationship()
    muc_tin_cay: Mapped[MucTinCay | None] = relationship()
    loai_lien_ket: Mapped[LoaiLienKet | None] = relationship()


class PhanHoiKetQua(Base):
    __tablename__ = "PhanHoiKetQua"
    __table_args__ = {"implicit_returning": False}

    phan_hoi_id: Mapped[int] = mapped_column("PhanHoiId", Integer, primary_key=True, autoincrement=True)
    ket_qua_du_doan_id: Mapped[int] = mapped_column("KetQuaDuDoanId", ForeignKey("KetQuaDuDoan.KetQuaDuDoanId"))
    nguoi_dung_id: Mapped[int | None] = mapped_column("NguoiDungId", ForeignKey("NguoiDung.NguoiDungId"))
    danh_gia: Mapped[str] = mapped_column("DanhGia", String(100))
    nhan_xet: Mapped[str | None] = mapped_column("NhanXet", String(1000))
    nguon_tham_khao_bo_sung: Mapped[str | None] = mapped_column("NguonThamKhaoBoSung", String(1000))
    trang_thai_xu_ly: Mapped[str] = mapped_column("TrangThaiXuLy", String(100), default="Chờ xử lý")
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)


class TapDuLieuHuanLuyen(Base):
    __tablename__ = "TapDuLieuHuanLuyen"
    __table_args__ = {"implicit_returning": False}

    tap_du_lieu_id: Mapped[int] = mapped_column("TapDuLieuId", Integer, primary_key=True, autoincrement=True)
    ma_tap_du_lieu: Mapped[str] = mapped_column("MaTapDuLieu", String(80))
    ten_tap_du_lieu: Mapped[str] = mapped_column("TenTapDuLieu", String(250))
    mo_ta: Mapped[str | None] = mapped_column("MoTa", String(1000))
    nguon_du_lieu_id: Mapped[int | None] = mapped_column("NguonDuLieuId", ForeignKey("NguonDuLieu.NguonDuLieuId"))
    so_luong_mau: Mapped[int | None] = mapped_column("SoLuongMau", Integer)
    ngay_tao: Mapped[datetime] = mapped_column("NgayTao", DateTime, default=now_utc)


class ChiTietTapDuLieu(Base):
    __tablename__ = "ChiTietTapDuLieu"
    __table_args__ = {"implicit_returning": False}

    chi_tiet_tap_du_lieu_id: Mapped[int] = mapped_column("ChiTietTapDuLieuId", Integer, primary_key=True, autoincrement=True)
    tap_du_lieu_id: Mapped[int] = mapped_column("TapDuLieuId", ForeignKey("TapDuLieuHuanLuyen.TapDuLieuId"))
    lien_ket_id: Mapped[int] = mapped_column("LienKetId", ForeignKey("LienKetThuocBenh.LienKetId"))
    nhan_huan_luyen: Mapped[int] = mapped_column("NhanHuanLuyen", Integer)
    ghi_chu: Mapped[str | None] = mapped_column("GhiChu", String(500))


class MoHinhMayHoc(Base):
    __tablename__ = "MoHinhMayHoc"
    __table_args__ = {"implicit_returning": False}

    mo_hinh_id: Mapped[int] = mapped_column("MoHinhId", Integer, primary_key=True, autoincrement=True)
    ma_mo_hinh: Mapped[str] = mapped_column("MaMoHinh", String(80), unique=True)
    ten_mo_hinh: Mapped[str] = mapped_column("TenMoHinh", String(250))
    phien_ban: Mapped[str] = mapped_column("PhienBan", String(80))
    thuat_toan: Mapped[str | None] = mapped_column("ThuatToan", String(150))
    tap_du_lieu_id: Mapped[int | None] = mapped_column("TapDuLieuId", ForeignKey("TapDuLieuHuanLuyen.TapDuLieuId"))
    ngay_huan_luyen: Mapped[datetime | None] = mapped_column("NgayHuanLuyen", DateTime)
    accuracy: Mapped[float | None] = mapped_column("Accuracy", Numeric(6, 5))
    precision_score: Mapped[float | None] = mapped_column("PrecisionScore", Numeric(6, 5))
    recall_score: Mapped[float | None] = mapped_column("RecallScore", Numeric(6, 5))
    f1_score: Mapped[float | None] = mapped_column("F1Score", Numeric(6, 5))
    auc_score: Mapped[float | None] = mapped_column("AucScore", Numeric(6, 5))
    duong_dan_tep_mo_hinh: Mapped[str | None] = mapped_column("DuongDanTepMoHinh", String(1000))
    dang_duoc_dung: Mapped[bool] = mapped_column("DangDuocDung", Boolean, default=False)
    ghi_chu: Mapped[str | None] = mapped_column("GhiChu", String(1000))


Drug = Thuoc
Disease = Benh
DrugDiseaseLink = LienKetThuocBenh
ConfidenceLevel = MucTinCay
LinkType = LoaiLienKet
EvidenceStatus = TrangThaiKiemDuyet
PredictionRequest = YeuCauDuDoan
PredictionResult = KetQuaDuDoan
PredictionFeedback = PhanHoiKetQua
ModelVersion = MoHinhMayHoc
