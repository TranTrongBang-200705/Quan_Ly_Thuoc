import { Activity, ChevronRight, Stethoscope } from "lucide-react";
import { truncate } from "../../utils/format";
import { Badge, Button, Card } from "../ui";

export function DiseaseCard({ disease, onDetail }) {
  const name = disease.tenBenh || disease.diseaseName;
  const group = disease.tenNhomBenh;

  return (
    <Card className="!p-4 space-y-3 flex flex-col" interactive>
      {/* Icon + Code */}
      <div className="flex items-start gap-3">
        <div className="w-11 h-11 rounded-[var(--radius-md)] bg-blue-50 flex items-center justify-center text-blue-600 shrink-0">
          <Stethoscope size={22} />
        </div>
        <div className="min-w-0">
          <Badge tone="blue" className="mb-1">
            {disease.maBenh || disease.diseaseCode || `ID ${disease.benhId || disease.diseaseId}`}
          </Badge>
          <h3 className="text-sm font-bold text-slate-900 m-0 leading-snug line-clamp-2">
            {name}
          </h3>
        </div>
      </div>

      {/* Synonyms */}
      {disease.tenDongNghia && (
        <p className="text-xs text-slate-500 m-0 line-clamp-1 leading-relaxed">
          {truncate(disease.tenDongNghia, 100)}
        </p>
      )}

      {/* Description */}
      {(disease.moTa || disease.description) && (
        <p className="text-xs text-slate-600 m-0 line-clamp-2 leading-relaxed">
          {truncate(disease.moTa || disease.description, 180)}
        </p>
      )}

      {/* Symptoms */}
      {disease.trieuChung && (
        <div className="flex items-start gap-1.5 text-xs text-slate-500">
          <Activity size={13} className="shrink-0 mt-0.5" />
          <span className="line-clamp-2">{truncate(disease.trieuChung, 130)}</span>
        </div>
      )}

      {/* Footer: group badge + drug count + detail button */}
      <div className="flex items-center justify-between gap-2 mt-auto pt-1">
        <div className="flex items-center gap-2 flex-wrap">
          {group ? (
            <Badge tone="slate">{group}</Badge>
          ) : (
            <Badge tone="amber">Đang phân loại</Badge>
          )}
          {disease.soThuocLienQuan != null && (
            <span className="text-[11px] text-slate-400 font-medium">
              {disease.soThuocLienQuan} thuốc
            </span>
          )}
        </div>

        {onDetail && (
          <Button
            variant="secondary"
            size="sm"
            className="shrink-0 !gap-1"
            onClick={() => onDetail(disease)}
          >
            Chi tiết
            <ChevronRight size={13} />
          </Button>
        )}
      </div>
    </Card>
  );
}
