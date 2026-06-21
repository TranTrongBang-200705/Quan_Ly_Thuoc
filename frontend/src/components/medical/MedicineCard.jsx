import { Building2, ChevronRight, Pill, ShieldCheck } from "lucide-react";
import { fallback, formatPercent, truncate } from "../../utils/format";
import { Badge, Button, Card } from "../ui";
import { DrugImage } from "./DrugImage";

export function MedicineCard({ drug, onDetail }) {
  const name = drug.tenThuoc || drug.drugName || drug.activeName;
  const image = drug.duongDanAnh || drug.drugImageUrl;

  return (
    <Card className="!p-0 overflow-hidden group flex flex-col" interactive>
      {/* Image */}
      <DrugImage src={image} alt={name} className="!rounded-b-none !border-x-0 !border-t-0" />

      {/* Body */}
      <div className="p-4 space-y-2.5 flex flex-col flex-1">
        {/* Code badge + name */}
        <div>
          <Badge tone="cyan" className="mb-1.5">
            {drug.maThuoc || drug.drugCode || `ID ${drug.thuocId || drug.drugId}`}
          </Badge>
          <h3 className="text-sm font-bold text-slate-900 m-0 leading-snug line-clamp-2">
            {name}
          </h3>
          {drug.hoatChat && (
            <p className="text-xs text-slate-500 mt-1 m-0 line-clamp-1">
              {drug.hoatChat}
            </p>
          )}
        </div>

        {/* Usage */}
        {(drug.congDung || drug.knownIndications) && (
          <p className="text-xs text-slate-600 leading-relaxed m-0 line-clamp-2">
            {truncate(drug.congDung || drug.knownIndications, 150)}
          </p>
        )}

        {/* Meta row */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500">
          {drug.nhaSanXuat && (
            <span className="inline-flex items-center gap-1">
              <Building2 size={13} />
              <span className="truncate max-w-[120px]">{drug.nhaSanXuat}</span>
            </span>
          )}
          {drug.dangBaoChe && (
            <span className="inline-flex items-center gap-1">
              <Pill size={13} />
              {drug.dangBaoChe}
            </span>
          )}
          {drug.tenTrangThaiKiemDuyet && (
            <span className="inline-flex items-center gap-1">
              <ShieldCheck size={13} />
              {drug.tenTrangThaiKiemDuyet}
            </span>
          )}
        </div>

        {/* Review strip */}
        {(drug.tyLeDanhGiaTot || drug.tyLeDanhGiaTrungBinh || drug.tyLeDanhGiaKem) && (
          <div className="flex flex-wrap gap-1.5">
            {drug.tyLeDanhGiaTot && (
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700">
                Tốt {formatPercent(drug.tyLeDanhGiaTot)}
              </span>
            )}
            {drug.tyLeDanhGiaTrungBinh && (
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700">
                TB {formatPercent(drug.tyLeDanhGiaTrungBinh)}
              </span>
            )}
            {drug.tyLeDanhGiaKem && (
              <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-50 text-red-700">
                Kém {formatPercent(drug.tyLeDanhGiaKem)}
              </span>
            )}
          </div>
        )}

        {/* Side effects */}
        {drug.tacDungPhu && (
          <p className="text-[11px] text-slate-400 m-0 line-clamp-2 leading-relaxed">
            Tác dụng phụ: {truncate(drug.tacDungPhu, 120)}
          </p>
        )}

        {!name && (
          <p className="text-xs text-slate-400 m-0">{fallback(drug.drugCode || drug.maThuoc)}</p>
        )}

        {/* Detail button — pushed to bottom */}
        {onDetail && (
          <div className="pt-1 mt-auto">
            <Button
              variant="secondary"
              size="sm"
              className="w-full !justify-between"
              onClick={() => onDetail(drug)}
            >
              <span>Xem chi tiết</span>
              <ChevronRight size={14} />
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}
