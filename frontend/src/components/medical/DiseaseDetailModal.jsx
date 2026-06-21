import { Activity, Hash, Info, ShieldCheck, Stethoscope, Tag } from "lucide-react";
import { Badge } from "../ui/Badge";
import { DetailModal } from "../ui/DetailModal";

function InfoCell({ label, value }) {
  if (!value) return null;
  return (
    <div className="p-3 rounded-xl border border-slate-100 bg-slate-50/60">
      <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wide">
        {label}
      </span>
      <p className="text-sm text-slate-800 font-medium mt-0.5 m-0 leading-snug">
        {value}
      </p>
    </div>
  );
}

export function DiseaseDetailModal({ disease, onClose }) {
  if (!disease) return null;

  const name = disease.tenBenh || disease.diseaseName;
  const group = disease.tenNhomBenh;
  const code = disease.maBenh || disease.diseaseCode;

  return (
    <DetailModal
      open={!!disease}
      onClose={onClose}
      eyebrow="Disease Knowledge"
      title={name || "Chi tiết bệnh/chỉ định"}
    >
      <div className="space-y-5">
        {/* Icon + Code + Badges */}
        <div className="flex gap-4 items-start">
          <div className="w-14 h-14 rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
            <Stethoscope size={26} />
          </div>
          <div className="min-w-0 space-y-2">
            <div className="flex flex-wrap gap-1.5">
              {code && (
                <Badge tone="blue">
                  <Hash size={11} />
                  {code}
                </Badge>
              )}
              {group ? (
                <Badge tone="slate">{group}</Badge>
              ) : (
                <Badge tone="amber">Đang phân loại</Badge>
              )}
            </div>
            <h3 className="text-base font-bold text-slate-900 m-0 leading-snug">
              {name}
            </h3>
            {disease.tenDongNghia && (
              <p className="text-sm text-slate-500 m-0 flex items-center gap-1">
                <Tag size={12} className="shrink-0 text-slate-400" />
                {disease.tenDongNghia}
              </p>
            )}
          </div>
        </div>

        {/* Info grid */}
        <div className="detail-info-grid">
          <InfoCell label="Mã bệnh" value={code} />
          <InfoCell label="Nhóm bệnh" value={group} />
          <InfoCell label="ICD Code" value={disease.icdCode || disease.maICD} />
          <InfoCell
            label="Số thuốc liên quan"
            value={
              disease.soThuocLienQuan != null
                ? `${disease.soThuocLienQuan} thuốc`
                : undefined
            }
          />
        </div>

        {/* Description */}
        {(disease.moTa || disease.description) && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0 flex items-center gap-1">
              <Info size={12} />
              Mô tả
            </h4>
            <p className="text-sm text-slate-700 leading-relaxed m-0 whitespace-pre-line">
              {disease.moTa || disease.description}
            </p>
          </div>
        )}

        {/* Symptoms */}
        {disease.trieuChung && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0 flex items-center gap-1">
              <Activity size={12} />
              Triệu chứng
            </h4>
            <p className="text-sm text-slate-700 leading-relaxed m-0 bg-blue-50/60 border border-blue-200/50 rounded-xl p-3">
              {disease.trieuChung}
            </p>
          </div>
        )}

        {/* Synonyms */}
        {disease.tenDongNghia && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
              Tên đồng nghĩa / Tên thường gọi
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed m-0">
              {disease.tenDongNghia}
            </p>
          </div>
        )}

        {/* Notes */}
        {disease.ghiChu && (
          <div className="space-y-1.5">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
              Ghi chú
            </h4>
            <p className="text-sm text-slate-600 leading-relaxed m-0">
              {disease.ghiChu}
            </p>
          </div>
        )}

        {/* Safety notice */}
        <div className="flex items-start gap-2 p-3 rounded-xl bg-blue-50/60 border border-blue-200/50 text-xs text-blue-800 leading-relaxed">
          <ShieldCheck size={14} className="shrink-0 mt-0.5 text-blue-600" />
          Dữ liệu bệnh/chỉ định được chuẩn hóa từ công dụng thuốc. Chỉ phục vụ
          học tập, nghiên cứu và tham khảo.
        </div>
      </div>
    </DetailModal>
  );
}
