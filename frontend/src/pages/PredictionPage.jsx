import {
  Beaker,
  Brain,
  CheckCircle2,
  Database,
  ListOrdered,
  Mail,
  Save,
  SlidersHorizontal,
  Sparkles,
  Target,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { api } from "../api";
import { MedicalWarning, PredictionResultCard, SystemStatusBadge } from "../components/medical";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  Input,
  LoadingSkeleton,
  Select,
} from "../components/ui";
import { useGsapReveal } from "../hooks/useGsapReveal";
import { useLoad } from "../hooks/useLoad";
import { useReducedMotion } from "../hooks/useReducedMotion";
import { getItems, normalizeApiError } from "../utils/format";

/* ── Workflow Steps ── */
const STEPS = [
  { icon: Database, label: "Chọn dữ liệu" },
  { icon: SlidersHorizontal, label: "Cấu hình ngưỡng" },
  { icon: Brain, label: "Phân tích AI" },
  { icon: ListOrdered, label: "Xếp hạng kết quả" },
];

/* ── Prediction type descriptions ── */
const TYPE_DESC = {
  DRUG_TO_DISEASE:
    "Chọn một thuốc đầu vào, hệ thống sẽ tìm các bệnh/chỉ định có liên kết tiềm năng.",
  DISEASE_TO_DRUG:
    "Chọn một bệnh/chỉ định, hệ thống sẽ tìm các thuốc có liên kết tiềm năng.",
  PAIR_PREDICTION:
    "Kiểm tra mức liên kết giữa một cặp thuốc-bệnh cụ thể.",
  PAIR_CHECK:
    "Kiểm tra mức liên kết giữa một cặp thuốc-bệnh cụ thể.",
};

const TYPE_LABEL = {
  DRUG_TO_DISEASE: "Từ thuốc tìm bệnh",
  DISEASE_TO_DRUG: "Từ bệnh tìm thuốc",
  PAIR_CHECK: "Kiểm tra một cặp",
  PAIR_PREDICTION: "Kiểm tra một cặp",
};

function toBackendPredictionType(type) {
  return type === "PAIR_CHECK" ? "PAIR_PREDICTION" : type;
}

export function PredictionPage({ user, health }) {
  const lookups = useLoad(() => api.getLookups(), []);
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 100 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 100 }), []);

  const [request, setRequest] = useState({
    predictionType: "DRUG_TO_DISEASE",
    drugId: "",
    diseaseId: "",
    topK: 10,
    scoreThreshold: "0.5",
    purpose: "Nghiên cứu liên kết thuốc - bệnh",
    contactEmail: user?.email || "",
    medicalWarningAccepted: false,
  });
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [apiError, setApiError] = useState("");
  const reducedMotion = useReducedMotion();
  const resultsRef = useRef(null);
  const errorRef = useRef(null);
  const results = response?.results ?? [];
  const formRevealRef = useGsapReveal({
    selector: "children",
    y: 18,
    duration: 0.38,
    stagger: 0.06,
  });
  const resultRevealRef = useGsapReveal({
    selector: "children",
    y: 16,
    duration: 0.34,
    stagger: 0.055,
    dependencies: [response?.yeuCauDuDoanId, response?.requestId, results?.length],
  });

  const predictionTypes = lookups.data?.predictionTypes ?? [
    { code: "DRUG_TO_DISEASE", name: "Từ thuốc tìm bệnh" },
    { code: "DISEASE_TO_DRUG", name: "Từ bệnh tìm thuốc" },
    { code: "PAIR_CHECK", name: "Kiểm tra một cặp thuốc - bệnh" },
  ];
  const drugItems = getItems(drugs.data);
  const diseaseItems = getItems(diseases.data);
  const drugImageById = useMemo(() => {
    const map = new Map();
    drugItems.forEach((drug) => {
      const id = drug.thuocId || drug.drugId;
      const image = drug.duongDanAnh || drug.drugImageUrl || drug.imageUrl || drug.image;
      if (id && image) map.set(String(id), image);
    });
    return map;
  }, [drugItems]);
  const isDrugDisabled = request.predictionType === "DISEASE_TO_DRUG";
  const isDiseaseDisabled = request.predictionType === "DRUG_TO_DISEASE";

  const assistantNote = useMemo(() => {
    if (
      response?.nguonDiem === "DATABASE_FALLBACK" ||
      response?.scoreSource === "DATABASE_FALLBACK"
    ) {
      return "AI service chưa khả dụng, hệ thống đang dùng điểm liên kết sẵn có trong database.";
    }
    return health?.aiStatus === "healthy"
      ? "AI service sẵn sàng. Kết quả được xếp hạng theo model và dữ liệu DataThuoc."
      : "AI service có thể chưa sẵn sàng. Backend sẽ fallback sang dữ liệu liên kết khi cần.";
  }, [health?.aiStatus, response]);

  const backendStatus = health?.status === "healthy" ? "online" : "offline";
  const databaseStatus = health?.status === "healthy" ? "healthy" : "unknown";
  const aiStatus = health?.aiStatus === "healthy" ? "ready" : "fallback";

  function scrollTo(ref, delay = 40) {
    window.setTimeout(() => {
      ref.current?.scrollIntoView({
        behavior: reducedMotion ? "auto" : "smooth",
        block: "start",
      });
    }, delay);
  }

  function update(key, value) {
    setRequest((current) => ({ ...current, [key]: value }));
  }

  function changeType(value) {
    setRequest((current) => ({
      ...current,
      predictionType: value,
      drugId: value === "DISEASE_TO_DRUG" ? "" : current.drugId,
      diseaseId: value === "DRUG_TO_DISEASE" ? "" : current.diseaseId,
    }));
    setError("");
  }

  function normalizeThreshold(raw) {
    /* Handle comma as decimal separator: "0,5" → "0.5" */
    return String(raw).replace(",", ".");
  }

  function validate() {
    if (!request.predictionType) return "Vui lòng chọn loại dự đoán.";
    const type = request.predictionType;

    if (type === "DRUG_TO_DISEASE" && !request.drugId)
      return "Vui lòng chọn thuốc đầu vào.";
    if (type === "DISEASE_TO_DRUG" && !request.diseaseId)
      return "Vui lòng chọn bệnh/chỉ định đầu vào.";
    if (
      (type === "PAIR_PREDICTION" || type === "PAIR_CHECK") &&
      (!request.drugId || !request.diseaseId)
    )
      return "Vui lòng chọn cả thuốc và bệnh/chỉ định để kiểm tra một cặp.";

    if (!request.medicalWarningAccepted)
      return "Vui lòng xác nhận cảnh báo y tế trước khi tạo dự đoán.";

    if (!request.contactEmail.trim()) return "Vui lòng nhập email liên hệ.";

    const topK = Number(request.topK);
    const threshold = Number(normalizeThreshold(request.scoreThreshold));

    if (!Number.isInteger(topK) || topK < 1 || topK > 100)
      return "Top K phải là số nguyên từ 1 đến 100.";
    if (Number.isNaN(threshold) || threshold < 0 || threshold > 1)
      return "Ngưỡng điểm phải là số từ 0 đến 1.";

    return "";
  }

  function buildPayload() {
    const type = request.predictionType;
    return {
      predictionType: toBackendPredictionType(type),
      drugId: type === "DISEASE_TO_DRUG" ? null : Number(request.drugId),
      diseaseId: type === "DRUG_TO_DISEASE" ? null : Number(request.diseaseId),
      topK: Number(request.topK),
      scoreThreshold: Number(normalizeThreshold(request.scoreThreshold)),
      purpose: request.purpose.trim() || null,
      contactEmail: request.contactEmail.trim(),
      medicalWarningAccepted: request.medicalWarningAccepted,
    };
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setApiError("");
    setResponse(null);
    const validation = validate();
    if (validation) {
      setError(validation);
      toast.error(validation);
      scrollTo(errorRef);
      return;
    }

    setSubmitting(true);
    setActiveStep(2);
    scrollTo(resultsRef);
    try {
      const data = await api.createPrediction(buildPayload());
      setResponse(data);
      setActiveStep(3);
      toast.success(
        `Phân tích hoàn tất: ${data.results?.length ?? 0} kết quả.`
      );
      scrollTo(resultsRef, 80);
    } catch (err) {
      const msg = normalizeApiError(err.message);
      setError(msg);
      setApiError(
        msg.includes("AI service")
          ? "AI service chưa khả dụng. Hệ thống đang dùng dữ liệu liên kết thay thế."
          : "Không thể hoàn tất phân tích lúc này. Vui lòng thử lại sau."
      );
      toast.error(msg);
      setActiveStep(0);
      scrollTo(errorRef);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-5">
      {/* ── Workflow Stepper ── */}
      <div className="flex items-center justify-center gap-2 sm:gap-4 flex-wrap">
        {STEPS.map((step, i) => {
          const StepIcon = step.icon;
          const done = i < activeStep;
          const current = i === activeStep;
          return (
            <div key={i} className="flex items-center gap-2 sm:gap-3">
              <div className="flex items-center gap-2">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                    done
                      ? "bg-teal-500 text-white"
                      : current
                        ? "bg-gradient-to-br from-teal-500 to-cyan-500 text-white shadow-md"
                        : "bg-slate-100 text-slate-400"
                  }`}
                >
                  {done ? <CheckCircle2 size={16} /> : <StepIcon size={14} />}
                </div>
                <span
                  className={`text-xs font-semibold hidden sm:inline ${
                    done || current ? "text-slate-800" : "text-slate-400"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className={`w-6 sm:w-10 h-0.5 rounded-full ${
                    done ? "bg-teal-400" : "bg-slate-200"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* ── Main Grid ── */}
      <div ref={formRevealRef} className="grid grid-cols-1 lg:grid-cols-[1.3fr,0.7fr] gap-5 items-start">
        {/* Left: Clinical Request Form */}
        <Card>
          <div className="mb-5">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              Clinical request
            </span>
            <h3 className="text-lg font-bold text-slate-900 m-0">
              Thiết lập phân tích
            </h3>
            <p className="text-sm text-slate-500 mt-1 m-0">
              Chọn dữ liệu đầu vào và ngưỡng điểm để hệ thống xếp hạng kết
              quả phù hợp.
            </p>
          </div>

          <form className="space-y-4" onSubmit={submit}>
            {/* Row 1: Prediction type */}
            <Select
              label="Loại dự đoán"
              icon={Beaker}
              value={request.predictionType}
              onChange={(e) => changeType(e.target.value)}
            >
              {predictionTypes.map((type) => (
                <option key={type.code} value={type.code}>
                  {type.name}
                </option>
              ))}
            </Select>

            {/* Type description */}
            <p className="text-xs text-slate-500 m-0 -mt-1 pl-1">
              {TYPE_DESC[request.predictionType] || ""}
            </p>

            {/* Row 2: Drug + Disease */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Select
                label="Thuốc đầu vào"
                disabled={isDrugDisabled || drugs.loading}
                value={request.drugId}
                onChange={(e) => update("drugId", e.target.value)}
              >
                <option value="">
                  {isDrugDisabled ? "Không cần chọn" : "Chọn thuốc"}
                </option>
                {drugItems.map((drug) => (
                  <option
                    key={drug.thuocId || drug.drugId}
                    value={drug.thuocId || drug.drugId}
                  >
                    {drug.tenThuoc || drug.drugName || drug.activeName}
                  </option>
                ))}
              </Select>

              <Select
                label="Bệnh/chỉ định đầu vào"
                disabled={isDiseaseDisabled || diseases.loading}
                value={request.diseaseId}
                onChange={(e) => update("diseaseId", e.target.value)}
              >
                <option value="">
                  {isDiseaseDisabled ? "Không cần chọn" : "Chọn bệnh/chỉ định"}
                </option>
                {diseaseItems.map((disease) => (
                  <option
                    key={disease.benhId || disease.diseaseId}
                    value={disease.benhId || disease.diseaseId}
                  >
                    {disease.tenBenh || disease.diseaseName}
                  </option>
                ))}
              </Select>
            </div>

            {/* Row 3: TopK + Threshold */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <Input
                label="Top K (số kết quả tối đa)"
                icon={SlidersHorizontal}
                type="number"
                min="1"
                max="100"
                value={request.topK}
                onChange={(e) => update("topK", e.target.value)}
              />
              <Input
                label="Ngưỡng điểm (0 – 1)"
                icon={Target}
                type="text"
                inputMode="decimal"
                value={request.scoreThreshold}
                onChange={(e) => update("scoreThreshold", e.target.value)}
                onBlur={(e) => update("scoreThreshold", normalizeThreshold(e.target.value))}
                placeholder="0.5"
              />
            </div>

            {/* Row 4: Email + Purpose */}
            <Input
              label="Email liên hệ"
              icon={Mail}
              type="email"
              value={request.contactEmail}
              onChange={(e) => update("contactEmail", e.target.value)}
            />
            <Input
              label="Mục đích phân tích"
              textarea
              value={request.purpose}
              onChange={(e) => update("purpose", e.target.value)}
              placeholder="Ví dụ: Nghiên cứu liên kết thuốc - bệnh cho luận văn..."
            />

            {/* Medical warning checkbox */}
            <label className="flex items-start gap-3 p-3 rounded-[var(--radius-md)] border border-emerald-200/60 bg-emerald-50/40 cursor-pointer hover:bg-emerald-50/70 transition-colors">
              <input
                type="checkbox"
                checked={request.medicalWarningAccepted}
                onChange={(e) =>
                  update("medicalWarningAccepted", e.target.checked)
                }
                className="w-5 h-5 mt-0.5 accent-teal-600 shrink-0"
              />
              <span className="text-sm text-emerald-800 leading-relaxed">
                Tôi xác nhận kết quả chỉ dùng để học tập, nghiên cứu và tham
                khảo. Không dùng để tự kê đơn hoặc thay thế tư vấn của bác
                sĩ/dược sĩ.
              </span>
            </label>

            {/* Error */}
            {error && (
              <div ref={errorRef}>
                <Alert tone="danger">{error}</Alert>
              </div>
            )}

            {/* Submit */}
            <div className="flex justify-end pt-1">
              <Button
                className="w-full sm:w-auto !h-11 px-5 shadow-[0_12px_26px_rgba(20,184,166,0.18)]"
                loading={submitting}
                disabled={submitting}
              >
                {submitting ? <Brain size={18} /> : <Sparkles size={18} />}
                {submitting ? "Đang phân tích..." : "Phân tích bằng AI"}
              </Button>
            </div>
          </form>
        </Card>

        {/* Right: AI Insight Panel */}
        <div className="space-y-4">
          <Card>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              AI Clinical Assistant
            </span>
            <h3 className="text-base font-bold text-slate-900 m-0 mb-3">
              Hỗ trợ diễn giải kết quả
            </h3>
            <p className="text-sm text-slate-600 m-0 leading-relaxed mb-4">
              {assistantNote}
            </p>

            {/* System status */}
            <div className="space-y-2 mb-4">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
                Trạng thái hệ thống
              </h4>
              <div className="flex flex-wrap gap-1.5">
                <SystemStatusBadge type="backend" status={backendStatus} />
                <SystemStatusBadge type="database" status={databaseStatus} />
                <SystemStatusBadge type="ai" status={aiStatus} />
              </div>
            </div>

            {/* Workflow steps */}
            <div className="space-y-2">
              <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
                Quy trình xử lý
              </h4>
              {[
                "Chuẩn hóa cặp thuốc-bệnh",
                "Chấm điểm bằng AI hoặc fallback",
                "Lưu vào YeuCauDuDoan và KetQuaDuDoan",
              ].map((step, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2.5 px-3 py-2.5 rounded-[var(--radius-md)] border border-blue-100 bg-blue-50/40 text-sm text-slate-700"
                >
                  <span className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xs font-bold shrink-0">
                    {i + 1}
                  </span>
                  {step}
                </div>
              ))}
            </div>

            {/* Source badge */}
            <div className="flex flex-wrap gap-1.5 mt-4">
              <Badge
                tone={health?.aiStatus === "healthy" ? "cyan" : "amber"}
              >
                {health?.aiStatus === "healthy"
                  ? "AI_MODEL"
                  : "DATABASE_FALLBACK"}
              </Badge>
              <Badge tone="emerald">Safety warning enabled</Badge>
            </div>
          </Card>

          <MedicalWarning />

          <Card className="!p-4">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-2">
              Analysis context
            </span>
            <div className="grid gap-2">
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  Clinical Safety
                </span>
                <strong className="text-xs text-slate-800">Đã bật cảnh báo</strong>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                  <Database size={14} className="text-cyan-500" />
                  Data Source
                </span>
                <strong className="text-xs text-slate-800">
                  {health?.aiStatus === "healthy" ? "AI + DataThuoc" : "Database fallback"}
                </strong>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                  <Target size={14} className="text-teal-500" />
                  Prediction Mode
                </span>
                <strong className="text-xs text-slate-800">
                  {TYPE_LABEL[request.predictionType] || request.predictionType}
                </strong>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 text-xs font-semibold text-slate-500">
                  <Save size={14} className="text-amber-500" />
                  Last analysis
                </span>
                <strong className="text-xs text-slate-800">
                  {response ? response.maYeuCau || response.requestCode : "Chưa có"}
                </strong>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* ── Results Section ── */}
      <div ref={resultsRef} className="scroll-mt-28 lg:scroll-mt-40">
      <Card>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
          <div>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              RANKED RESULTS
            </span>
            <h3 className="text-lg font-bold text-slate-900 m-0">
              Kết quả dự đoán
            </h3>
            <p className="text-sm text-slate-500 mt-1 m-0">
              {submitting
                ? "Hệ thống đang phân tích và xếp hạng kết quả phù hợp."
                : response
                  ? `Tìm thấy ${results.length} kết quả phù hợp.`
                  : "Kết quả xếp hạng sẽ hiển thị sau khi phân tích."}
            </p>
          </div>
          {response && (
            <Badge tone="cyan">
              {response.maYeuCau || response.requestCode}
            </Badge>
          )}
        </div>

        {submitting ? (
          <div className="space-y-3">
            <Alert tone="info">
              Đang phân tích dữ liệu lâm sàng và xếp hạng kết quả phù hợp...
            </Alert>
            <LoadingSkeleton count={3} variant="row" />
          </div>
        ) : apiError ? (
          <Alert tone="danger">{apiError}</Alert>
        ) : !response ? (
          <EmptyState icon={Sparkles} title="Chưa có kết quả">
            Kết quả xếp hạng sẽ xuất hiện ở đây sau khi bạn gửi yêu cầu phân
            tích.
          </EmptyState>
        ) : results.length === 0 ? (
          <EmptyState icon={Sparkles} title="Không tìm thấy liên kết phù hợp">
            Không tìm thấy liên kết phù hợp với ngưỡng điểm hiện tại. Hãy thử
            giảm ngưỡng hoặc chọn dữ liệu khác.
          </EmptyState>
        ) : (
          <div ref={resultRevealRef} className="space-y-3">
            {results.map((result, i) => (
              <PredictionResultCard
                key={result.ketQuaDuDoanId || result.predictionResultId || i}
                result={result}
                index={i}
                drugImage={drugImageById.get(String(result.thuocId || result.drugId))}
              />
            ))}
          </div>
        )}
      </Card>
      </div>
    </section>
  );
}
