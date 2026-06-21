import clsx from "clsx";
import { ArrowRight, Brain, DatabaseZap, ShieldAlert } from "lucide-react";
import {
  DEFAULT_EXPLANATION_MESSAGE,
  FALLBACK_SOURCE_MESSAGE,
  STANDARD_MEDICAL_WARNING,
  formatScore,
  sanitizeClinicalText,
  truncate,
} from "../../utils/format";
import { Badge, Card } from "../ui";
import { DrugImage } from "./DrugImage";
import { MEDICAL_WARNING } from "./MedicalWarning";

function sourceTone(source) {
  if (source === "DATABASE_FALLBACK") return "amber";
  if (source === "AI_MODEL") return "cyan";
  return "slate";
}

function confidenceTone(value) {
  const text = String(value || "").toLowerCase();
  if (text.includes("cao") || text.includes("high")) return "emerald";
  if (text.includes("trung") || text.includes("medium")) return "blue";
  return "slate";
}

function ScoreBar({ score }) {
  const pct = Math.round(Math.min(Math.max(Number(score) * 100, 0), 100));
  const color =
    pct >= 70 ? "bg-emerald-500" : pct >= 40 ? "bg-blue-500" : "bg-slate-400";
  return (
    <div className="score-bar-track mt-1.5">
      <div
        className={`score-bar-fill ${color}`}
        style={{ width: `${pct}%` }}
      />
    </div>
  );
}

function resultImage(result, drugImage) {
  return (
    result.duongDanAnh ||
    result.drugImageUrl ||
    result.imageUrl ||
    result.image ||
    result.image_url ||
    result.medicineImage ||
    result.thuoc?.duongDanAnh ||
    result.drug?.duongDanAnh ||
    drugImage ||
    ""
  );
}

export function PredictionResultCard({ result, index = 0, drugImage = "" }) {
  const rank = result.thuHang || result.rankNo;
  const score = result.diemDuDoan ?? result.predictionScore;
  const source = result.nguonDiem || result.scoreSource || "UNKNOWN";
  const confidence =
    result.tenMucTinCay || result.confidenceLevel || "Đang phân loại";
  const linkType =
    result.tenLoaiLienKet || result.linkType || "Đang phân loại";
  const drugName = result.tenThuoc || result.drugName;
  const diseaseName = result.tenBenh || result.diseaseName;
  const isFallback = source === "DATABASE_FALLBACK";
  const scoreNum = Number(score);
  const image = resultImage(result, drugImage);
  const explanation = sanitizeClinicalText(
    result.giaiThichNgan || result.explanationText,
    isFallback ? FALLBACK_SOURCE_MESSAGE : DEFAULT_EXPLANATION_MESSAGE,
  );
  const warning = sanitizeClinicalText(
    result.canhBao ||
      result.systemWarning ||
      result.canhBaoYTe ||
      result.warningText,
    STANDARD_MEDICAL_WARNING,
  );
  const scoreLabel = isFallback ? "Điểm liên kết" : "Điểm AI";
  const isDefaultScore = isFallback && Math.abs(scoreNum - 0.65) < 0.00001;

  return (
    <Card
      className="!p-0 overflow-hidden result-card-animated border-slate-200/80"
      style={{ animationDelay: `${index * 80}ms` }}
    >
      <div className="grid gap-4 p-4 sm:grid-cols-[35%_minmax(0,1fr)] sm:items-start">
        <div className="order-2 flex items-center justify-between gap-3 rounded-2xl border border-slate-100 bg-gradient-to-br from-slate-50 to-cyan-50/40 p-3 sm:col-start-2 sm:order-2">
          <span className="w-11 h-11 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 text-white text-sm font-black flex items-center justify-center shadow-sm shrink-0">
            #{rank}
          </span>
          <div className="min-w-[132px] text-right sm:text-center">
            <strong
              className={clsx(
                "block text-2xl font-black leading-none tabular-nums",
                scoreNum >= 0.7
                  ? "text-emerald-600"
                  : scoreNum >= 0.4
                    ? "text-blue-600"
                    : "text-slate-500"
              )}
            >
              {formatScore(score)}
            </strong>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
              {scoreLabel}
            </span>
            <ScoreBar score={scoreNum} />
          </div>
        </div>

        <div className="order-1 min-w-0 sm:col-start-1 sm:row-span-2 sm:order-1">
          <DrugImage
            src={image}
            alt={drugName}
            className="!aspect-auto h-[176px] sm:h-[210px] lg:h-[220px] !rounded-2xl"
          />
        </div>

        <div className="order-3 min-w-0 space-y-3 sm:col-start-2 sm:order-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 m-0 leading-snug line-clamp-2">
              {drugName}
            </h3>
            <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500">
              <ArrowRight size={13} className="shrink-0 text-teal-500" />
              <span className="line-clamp-1 font-medium">{diseaseName}</span>
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <Badge tone={sourceTone(source)}>
              {isFallback ? (
                <DatabaseZap size={12} />
              ) : (
                <Brain size={12} />
              )}
              {isFallback ? "Database Fallback" : "AI Model"}
            </Badge>
            <Badge tone={confidenceTone(confidence)}>{confidence}</Badge>
            {linkType && linkType !== "Đang phân loại" && (
              <Badge tone={linkType.toLowerCase().includes("chỉ định") ? "blue" : "slate"}>
                {linkType}
              </Badge>
            )}
            {isDefaultScore && (
              <Badge tone="amber">Điểm mặc định từ dữ liệu liên kết</Badge>
            )}
          </div>

          {explanation && (
            <p className="text-xs text-slate-600 m-0 leading-relaxed line-clamp-3">
              {truncate(explanation, 280)}
            </p>
          )}

          {warning && warning !== MEDICAL_WARNING && warning !== STANDARD_MEDICAL_WARNING && (
            <div className="flex items-start gap-1.5 text-[11px] text-amber-700 bg-amber-50/70 rounded-lg px-2.5 py-1.5">
              <ShieldAlert size={13} className="shrink-0 mt-0.5" />
              <span className="line-clamp-2">{truncate(warning, 200)}</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
