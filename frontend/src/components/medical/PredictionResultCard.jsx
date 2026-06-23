import clsx from "clsx";
import { ArrowRight, Brain, CheckCircle2, DatabaseZap, ShieldAlert } from "lucide-react";
import {
  DEFAULT_EXPLANATION_MESSAGE,
  FALLBACK_SOURCE_MESSAGE,
  STANDARD_MEDICAL_WARNING,
  formatScore,
  inferConfidenceFromScore,
  inferLinkConclusion,
  parseNumberInput,
  sanitizeClinicalText,
  truncate,
} from "../../utils/format";
import { Badge, Card } from "../ui";
import { DrugImage } from "./DrugImage";

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
  const numericScore = Number.isFinite(score) ? score : 0;
  const pct = Math.round(Math.min(Math.max(numericScore * 100, 0), 100));
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

export function PredictionResultCard({
  result,
  index = 0,
  drugImage = "",
  mode = "DRUG_TO_DISEASE",
}) {
  const rank = result.thuHang || result.rankNo || index + 1;
  const score = result.diemDuDoan ?? result.predictionScore;
  const source = result.nguonDiem || result.scoreSource || "UNKNOWN";
  const confidence =
    result.tenMucTinCay ||
    result.confidenceLevel ||
    inferConfidenceFromScore(score);
  const linkType =
    result.tenLoaiLienKet || result.linkType || "Đang phân loại";
  const drugName = result.tenThuoc || result.drugName;
  const diseaseName = result.tenBenh || result.diseaseName;
  const drugIndication =
    result.congDung ||
    result.knownIndications ||
    result.indication ||
    result.drugIndication;
  const isFallback = source === "DATABASE_FALLBACK";
  const scoreNum = parseNumberInput(score);
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
  const isDefaultScore = isFallback && Number.isFinite(scoreNum) && Math.abs(scoreNum - 0.65) < 0.00001;
  const isDiseaseToDrug = mode === "DISEASE_TO_DRUG";
  const inputLabel = isDiseaseToDrug ? "Bệnh/chỉ định đầu vào" : "Thuốc đầu vào";
  const inputName = isDiseaseToDrug ? diseaseName : drugName;
  const suggestionLabel = isDiseaseToDrug
    ? "Thuốc được gợi ý"
    : "Bệnh/chỉ định được gợi ý";
  const suggestionName = isDiseaseToDrug ? drugName : diseaseName;

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
            <p className="text-[11px] font-bold uppercase tracking-wide text-slate-400 m-0">
              {inputLabel}
            </p>
            <h3 className="text-sm font-bold text-slate-900 m-0 leading-snug line-clamp-2">
              {inputName || "-"}
            </h3>
            <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500">
              <ArrowRight size={13} className="shrink-0 text-teal-500" />
              <span className="line-clamp-1 font-medium">
                {suggestionLabel}: {suggestionName || "-"}
              </span>
            </div>
            {drugIndication && (
              <div className="mt-2 rounded-xl border border-teal-100 bg-teal-50/45 px-3 py-2">
                <p className="m-0 text-[11px] font-bold uppercase tracking-wide text-teal-700">
                  Công dụng thuốc
                </p>
                <p className="m-0 mt-1 text-xs leading-relaxed text-slate-700 line-clamp-3">
                  {truncate(drugIndication, 260)}
                </p>
              </div>
            )}
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

          {warning && (
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

function conclusionTone(conclusion) {
  const text = String(conclusion || "").toLowerCase();
  if (text.includes("mạnh")) return "emerald";
  if (text.includes("trung bình")) return "blue";
  return "amber";
}

function DetailRow({ label, value }) {
  if (!value) return null;
  return (
    <div className="rounded-xl border border-slate-100 bg-slate-50/70 p-3">
      <dt className="text-[11px] font-bold uppercase tracking-wide text-slate-400">
        {label}
      </dt>
      <dd className="mt-1 break-words text-sm font-semibold text-slate-800 m-0">
        {value}
      </dd>
    </div>
  );
}

export function PairCheckResultPanel({ result, drugImage = "" }) {
  const score = result?.diemDuDoan ?? result?.predictionScore;
  const scoreNum = parseNumberInput(score);
  const confidence =
    result?.tenMucTinCay ||
    result?.confidenceLevel ||
    inferConfidenceFromScore(score);
  const linkType = result?.tenLoaiLienKet || result?.linkType;
  const drugName = result?.tenThuoc || result?.drugName;
  const diseaseName = result?.tenBenh || result?.diseaseName;
  const drugIndication =
    result?.congDung ||
    result?.knownIndications ||
    result?.indication ||
    result?.drugIndication;
  const source = result?.nguonDiem || result?.scoreSource || "UNKNOWN";
  const isFallback = source === "DATABASE_FALLBACK";
  const image = resultImage(result || {}, drugImage);
  const conclusion = inferLinkConclusion(
    score,
    result?.ketLuan || result?.conclusion || result?.resultConclusion,
  );
  const explanation = sanitizeClinicalText(
    result?.giaiThichNgan || result?.explanationText,
    isFallback ? FALLBACK_SOURCE_MESSAGE : DEFAULT_EXPLANATION_MESSAGE,
  );
  const warning = sanitizeClinicalText(
    result?.canhBao ||
      result?.systemWarning ||
      result?.canhBaoYTe ||
      result?.warningText,
    STANDARD_MEDICAL_WARNING,
  );

  return (
    <Card className="!p-0 overflow-hidden border-slate-200/80">
      <div className="grid gap-5 p-4 sm:grid-cols-[220px_minmax(0,1fr)]">
        <DrugImage
          src={image}
          alt={drugName}
          className="h-[180px] sm:h-full min-h-[180px] !rounded-2xl"
        />

        <div className="min-w-0 space-y-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-xs font-bold uppercase tracking-wide text-teal-600 m-0">
                Kết luận AI cho một cặp cụ thể
              </p>
              <h3 className="mt-1 text-lg font-extrabold text-slate-900 m-0">
                {drugName || "-"} → {diseaseName || "-"}
              </h3>
            </div>
            <div className="rounded-2xl bg-gradient-to-br from-teal-50 to-cyan-50 px-4 py-3 text-right">
              <strong className="block text-3xl font-black tabular-nums text-teal-700">
                {formatScore(score)}
              </strong>
              <span className="text-[11px] font-bold uppercase tracking-wide text-slate-400">
                Điểm AI
              </span>
              <ScoreBar score={scoreNum} />
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <Badge tone={conclusionTone(conclusion)}>
              <CheckCircle2 size={12} />
              {conclusion}
            </Badge>
            <Badge tone={confidenceTone(confidence)}>{confidence}</Badge>
            {linkType && <Badge tone="slate">{linkType}</Badge>}
            <Badge tone={sourceTone(source)}>
              {isFallback ? <DatabaseZap size={12} /> : <Brain size={12} />}
              {isFallback ? "Database Fallback" : "AI Model"}
            </Badge>
          </div>

          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <DetailRow label="Thuốc" value={drugName} />
            <DetailRow label="Bệnh/chỉ định" value={diseaseName} />
            <DetailRow label="Công dụng thuốc" value={drugIndication} />
            <DetailRow label="Mức tin cậy" value={confidence} />
            <DetailRow label="Loại liên kết" value={linkType} />
          </dl>

          {explanation && (
            <p className="rounded-xl border border-slate-100 bg-slate-50/70 p-3 text-sm leading-relaxed text-slate-600 m-0">
              {truncate(explanation, 360)}
            </p>
          )}

          {warning && (
            <div className="flex items-start gap-2 rounded-xl border border-amber-200/70 bg-amber-50/80 p-3 text-xs leading-relaxed text-amber-800">
              <ShieldAlert size={15} className="mt-0.5 shrink-0" />
              <span>{truncate(warning, 260)}</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
