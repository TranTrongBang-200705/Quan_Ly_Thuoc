import { Building2, Pill, ShieldCheck, Tag, Zap } from "lucide-react";
import { Badge } from "../ui/Badge";
import { DetailModal } from "../ui/DetailModal";
import { DrugImage } from "./DrugImage";

function InfoCell({ label, value }) {
  if (!value) return null;
  return (
    <div className="p-3 rounded-xl border border-slate-100 bg-slate-50/60">
      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
        {label}
      </span>
      <p className="text-sm text-slate-800 font-medium mt-0.5 m-0 leading-snug break-words">
        {value}
      </p>
    </div>
  );
}

export function DrugDetailModal({ drug, onClose }) {
  if (!drug) return null;

  const name = drug.tenThuoc || drug.drugName || drug.activeName;
  const image = drug.duongDanAnh || drug.drugImageUrl;

  return (
    <DetailModal
      open={!!drug}
      onClose={onClose}
      eyebrow="Drug Discovery"
      title={name || "Chi tiết thuốc"}
    >
      <div className="space-y-5">
        {/* Image + code + badges */}
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start">
          <DrugImage
            src={image}
            alt={name}
            className="h-44 w-full shrink-0 !rounded-2xl sm:h-36 sm:w-40"
          />
          <div className="min-w-0 space-y-2 break-words">
            <div className="flex flex-wrap gap-1.5">
              <Badge tone="cyan">
                {drug.maThuoc || drug.drugCode || `ID ${drug.thuocId || drug.drugId}`}
              </Badge>
              {drug.tenTrangThaiKiemDuyet && (
                <Badge tone="emerald">
                  <ShieldCheck size={11} />
                  {drug.tenTrangThaiKiemDuyet}
                </Badge>
              )}
              {drug.dangBaoChe && (
                <Badge tone="slate">
                  <Pill size={11} />
                  {drug.dangBaoChe}
                </Badge>
              )}
            </div>
            <h3 className="text-base font-bold text-slate-900 m-0 leading-snug">
              {name}
            </h3>
            {drug.hoatChat && (
              <p className="text-sm text-slate-500 m-0 flex items-center gap-1">
                <Zap size={13} className="shrink-0 text-teal-500" />
                {drug.hoatChat}
              </p>
            )}
            {drug.nhaSanXuat && (
              <p className="text-sm text-slate-500 m-0 flex items-center gap-1">
                <Building2 size={13} className="shrink-0 text-slate-400" />
                {drug.nhaSanXuat}
              </p>
            )}
          </div>
        </div>

        {/* Info grid */}
        <div className="detail-info-grid">
          <InfoCell label="Mã thuốc" value={drug.maThuoc || drug.drugCode} />
          <InfoCell label="Dạng bào chế" value={drug.dangBaoChe} />
          <InfoCell label="Nhà sản xuất" value={drug.nhaSanXuat} />
          <InfoCell label="Nước sản xuất" value={drug.nuocSanXuat} />
          <InfoCell label="Số đăng ký" value={drug.soDangKy} />
          <InfoCell label="Nhóm thuốc" value={drug.tenNhomThuoc} />
        </div>

        {/* Full usage */}
        {(drug.congDung || drug.knownIndications) && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
              Công dụng / Chỉ định
            </h4>
            <p className="text-sm text-slate-700 leading-relaxed m-0 whitespace-pre-line break-words">
              {drug.congDung || drug.knownIndications}
            </p>
          </div>
        )}

        {/* Side effects */}
        {drug.tacDungPhu && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0 flex items-center gap-1">
              <Tag size={12} />
              Tác dụng phụ
            </h4>
            <p className="text-sm text-amber-800 leading-relaxed m-0 bg-amber-50/60 border border-amber-200/50 rounded-xl p-3 whitespace-pre-line break-words">
              {drug.tacDungPhu}
            </p>
          </div>
        )}

        {/* Contraindications */}
        {drug.chongChiDinh && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
              Chống chỉ định
            </h4>
            <p className="text-sm text-red-800 leading-relaxed m-0 bg-red-50/60 border border-red-200/50 rounded-xl p-3 whitespace-pre-line break-words">
              {drug.chongChiDinh}
            </p>
          </div>
        )}

        {/* Review stats */}
        {(drug.tyLeDanhGiaTot || drug.tyLeDanhGiaTrungBinh || drug.tyLeDanhGiaKem) && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
              Đánh giá từ người dùng
            </h4>
            <div className="flex gap-2 flex-wrap">
              {drug.tyLeDanhGiaTot && (
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/50">
                  Tốt {drug.tyLeDanhGiaTot}%
                </span>
              )}
              {drug.tyLeDanhGiaTrungBinh && (
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200/50">
                  Trung bình {drug.tyLeDanhGiaTrungBinh}%
                </span>
              )}
              {drug.tyLeDanhGiaKem && (
                <span className="text-xs font-bold px-3 py-1 rounded-full bg-red-50 text-red-700 border border-red-200/50">
                  Kém {drug.tyLeDanhGiaKem}%
                </span>
              )}
            </div>
          </div>
        )}

        {/* Medical safety notice */}
        <div className="flex items-start gap-2 p-3 rounded-xl bg-emerald-50/60 border border-emerald-200/50 text-xs text-emerald-800 leading-relaxed">
          <ShieldCheck size={14} className="shrink-0 mt-0.5 text-emerald-600" />
          Thông tin chỉ phục vụ học tập, nghiên cứu và tham khảo. Không thay
          thế tư vấn của bác sĩ hoặc dược sĩ.
        </div>
      </div>
    </DetailModal>
  );
}
