import {
  Beaker,
  Brain,
  CheckCircle2,
  Database,
  ListOrdered,
  Pill,
  ShieldAlert,
  Sparkles,
  Stethoscope,
} from "lucide-react";
import { useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { api } from "../api";
import {
  MedicalWarning,
  PairCheckResultPanel,
  PredictionResultCard,
  SystemStatusBadge,
} from "../components/medical";
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
import {
  getItems,
  normalizeApiError,
  normalizePredictionType,
  parseNumberInput,
} from "../utils/format";

const MODE_OPTIONS = [
  {
    code: "DRUG_TO_DISEASE",
    label: "Từ thuốc tìm bệnh/chỉ định",
    shortLabel: "Từ thuốc tìm bệnh",
    description: "AI xếp hạng các bệnh/chỉ định liên quan đến thuốc đã chọn.",
    actionLabel: "Tìm bệnh/chỉ định liên quan",
    resultTitle: "Bệnh/chỉ định được AI xếp hạng",
    emptyTitle: "Chưa có bệnh/chỉ định phù hợp",
  },
  {
    code: "DISEASE_TO_DRUG",
    label: "Từ bệnh/chỉ định tìm thuốc",
    shortLabel: "Từ bệnh tìm thuốc",
    description: "AI xếp hạng các thuốc liên quan đến bệnh/chỉ định đã chọn.",
    actionLabel: "Tìm thuốc liên quan",
    resultTitle: "Thuốc được AI xếp hạng",
    emptyTitle: "Chưa có thuốc phù hợp",
  },
  {
    code: "PAIR_CHECK",
    label: "Kiểm tra một cặp thuốc-bệnh",
    shortLabel: "Kiểm tra cặp",
    description: "AI đánh giá một cặp thuốc-bệnh cụ thể và đưa ra kết luận.",
    actionLabel: "Kiểm tra liên kết",
    resultTitle: "Kết quả kiểm tra liên kết",
    emptyTitle: "Chưa có kết quả kiểm tra",
  },
];

const WORKFLOW_STEPS = [
  { icon: Database, title: "Chọn thuốc hoặc bệnh" },
  { icon: Brain, title: "AI chấm điểm liên kết" },
  { icon: ListOrdered, title: "Xếp hạng hoặc kết luận" },
];

const AI_EXPLANATIONS = [
  {
    title: "Từ thuốc tìm bệnh",
    body: "AI xếp hạng các bệnh/chỉ định liên quan đến thuốc.",
  },
  {
    title: "Từ bệnh tìm thuốc",
    body: "AI xếp hạng các thuốc liên quan đến bệnh/chỉ định.",
  },
  {
    title: "Kiểm tra cặp",
    body: "AI đánh giá một cặp thuốc-bệnh cụ thể.",
  },
];

function modeMeta(code) {
  const normalized = normalizePredictionType(code);
  return MODE_OPTIONS.find((item) => item.code === normalized) ?? MODE_OPTIONS[0];
}

function positiveId(value) {
  const number = Number(value);
  return Number.isInteger(number) && number > 0 ? number : null;
}

function validTopK(value) {
  const number = parseNumberInput(value);
  if (!Number.isInteger(number) || number < 1 || number > 100) return null;
  return number;
}

export function PredictionPage({ user, health }) {
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 100 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 100 }), []);

  const [request, setRequest] = useState({
    predictionType: "DRUG_TO_DISEASE",
    drugId: "",
    diseaseId: "",
    topK: 10,
    medicalWarningAccepted: false,
  });
  const [submittedType, setSubmittedType] = useState("");
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const reducedMotion = useReducedMotion();
  const resultsRef = useRef(null);
  const errorRef = useRef(null);
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
    dependencies: [response?.yeuCauDuDoanId, response?.requestId, response?.results?.length],
  });

  const mode = normalizePredictionType(request.predictionType);
  const meta = modeMeta(mode);
  const showDrug = mode !== "DISEASE_TO_DRUG";
  const showDisease = mode !== "DRUG_TO_DISEASE";
  const showTopK = mode !== "PAIR_CHECK";
  const drugItems = getItems(drugs.data);
  const diseaseItems = getItems(diseases.data);
  const results = response?.results ?? [];
  const resultMode = normalizePredictionType(
    response?.kieuDuDoan || response?.predictionType || submittedType || mode,
  );
  const resultMeta = modeMeta(resultMode);

  const drugImageById = useMemo(() => {
    const map = new Map();
    drugItems.forEach((drug) => {
      const id = drug.thuocId || drug.drugId;
      const image = drug.duongDanAnh || drug.drugImageUrl || drug.imageUrl || drug.image;
      if (id && image) map.set(String(id), image);
    });
    return map;
  }, [drugItems]);

  const backendStatus = health?.status === "healthy" ? "online" : "offline";
  const databaseStatus = health?.status === "healthy" ? "healthy" : "unknown";
  const aiStatus = health?.aiStatus === "healthy" ? "ready" : "fallback";
  const assistantNote =
    "AI service sử dụng mô hình Machine Learning để chấm điểm khả năng liên kết giữa thuốc và bệnh/chỉ định từ dữ liệu DataThuoc.";

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

  function changeType(rawValue) {
    const value = normalizePredictionType(rawValue);
    setRequest((current) => ({
      ...current,
      predictionType: value,
      drugId: value === "DISEASE_TO_DRUG" ? "" : current.drugId,
      diseaseId: value === "DRUG_TO_DISEASE" ? "" : current.diseaseId,
      topK: value === "PAIR_CHECK" ? 1 : current.topK || 10,
    }));
    setError("");
  }

  function validate() {
    if (mode === "DRUG_TO_DISEASE" && !positiveId(request.drugId)) {
      return "Vui lòng chọn thuốc đầu vào.";
    }
    if (mode === "DISEASE_TO_DRUG" && !positiveId(request.diseaseId)) {
      return "Vui lòng chọn bệnh/chỉ định đầu vào.";
    }
    if (mode === "PAIR_CHECK" && (!positiveId(request.drugId) || !positiveId(request.diseaseId))) {
      return "Vui lòng chọn cả thuốc và bệnh/chỉ định để kiểm tra một cặp.";
    }
    if (showTopK && validTopK(request.topK) === null) {
      return "Số kết quả muốn xem phải là số nguyên từ 1 đến 100.";
    }
    if (!request.medicalWarningAccepted) {
      return "Vui lòng xác nhận cảnh báo y khoa trước khi tạo dự đoán.";
    }
    return "";
  }

  function buildPayload() {
    return {
      predictionType: mode,
      drugId: mode === "DISEASE_TO_DRUG" ? null : positiveId(request.drugId),
      diseaseId: mode === "DRUG_TO_DISEASE" ? null : positiveId(request.diseaseId),
      topK: mode === "PAIR_CHECK" ? 1 : validTopK(request.topK),
      scoreThreshold: 0,
      purpose: "Dự đoán liên kết thuốc-bệnh",
      contactEmail: null,
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
    setSubmittedType(mode);
    scrollTo(resultsRef);
    try {
      const data = await api.createPrediction(buildPayload());
      setResponse(data);
      toast.success(
        mode === "PAIR_CHECK"
          ? "Đã kiểm tra liên kết thuốc-bệnh."
          : `AI đã xếp hạng ${data.results?.length ?? 0} kết quả.`,
      );
      scrollTo(resultsRef, 80);
    } catch (err) {
      const msg = normalizeApiError(err.message);
      setError(msg);
      setApiError(
        msg.includes("AI service")
          ? "AI service chưa khả dụng. Backend sẽ xử lý theo cơ chế dự phòng hiện có."
          : "Không thể hoàn tất phân tích lúc này. Vui lòng thử lại sau.",
      );
      toast.error(msg);
      scrollTo(errorRef);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-5">
      <Card>
        <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
          Machine Learning
        </span>
        <h2 className="text-xl font-extrabold text-slate-900 m-0">
          RandomForest chấm điểm liên kết thuốc-bệnh
        </h2>
        <p className="text-sm text-slate-500 mt-1.5 m-0 max-w-3xl leading-relaxed">
          AI service sử dụng mô hình Machine Learning để chấm điểm khả năng liên
          kết giữa thuốc và bệnh/chỉ định từ dữ liệu DataThuoc.
        </p>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {WORKFLOW_STEPS.map((step, index) => {
          const Icon = step.icon;
          return (
            <Card key={step.title} className="!p-4">
              <div className="flex items-center gap-3">
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-teal-50 text-teal-700">
                  <Icon size={19} />
                </span>
                <div>
                  <p className="text-xs font-bold uppercase tracking-wide text-slate-400 m-0">
                    Bước {index + 1}
                  </p>
                  <h3 className="text-sm font-extrabold text-slate-900 m-0">
                    {step.title}
                  </h3>
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      <div ref={formRevealRef} className="grid grid-cols-1 lg:grid-cols-[1.25fr,0.75fr] gap-5 items-start">
        <Card>
          <div className="mb-5">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              RandomForest scoring
            </span>
            <h2 className="text-lg font-bold text-slate-900 m-0">
              Thiết lập dự đoán
            </h2>
            <p className="text-sm text-slate-500 mt-1 m-0">
              Chọn đúng mode AI. Các trường kỹ thuật được gửi mặc định theo
              contract backend và không hiển thị trong form người dùng.
            </p>
          </div>

          <form className="space-y-4" onSubmit={submit}>
            <Select
              label="Loại dự đoán"
              icon={Beaker}
              value={mode}
              onChange={(event) => changeType(event.target.value)}
            >
              {MODE_OPTIONS.map((type) => (
                <option key={type.code} value={type.code}>
                  {type.label}
                </option>
              ))}
            </Select>

            <p className="text-xs text-slate-500 m-0 -mt-1 pl-1">
              {meta.description}
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {showDrug && (
                <Select
                  label="Thuốc đầu vào"
                  value={request.drugId}
                  disabled={drugs.loading}
                  onChange={(event) => update("drugId", event.target.value)}
                >
                  <option value="">Chọn thuốc</option>
                  {drugItems.map((drug) => (
                    <option
                      key={drug.thuocId || drug.drugId}
                      value={drug.thuocId || drug.drugId}
                    >
                      {drug.tenThuoc || drug.drugName || drug.activeName}
                    </option>
                  ))}
                </Select>
              )}

              {showDisease && (
                <Select
                  label="Bệnh/chỉ định đầu vào"
                  value={request.diseaseId}
                  disabled={diseases.loading}
                  onChange={(event) => update("diseaseId", event.target.value)}
                >
                  <option value="">Chọn bệnh/chỉ định</option>
                  {diseaseItems.map((disease) => (
                    <option
                      key={disease.benhId || disease.diseaseId}
                      value={disease.benhId || disease.diseaseId}
                    >
                      {disease.tenBenh || disease.diseaseName}
                    </option>
                  ))}
                </Select>
              )}
            </div>

            {showTopK && (
              <div className="space-y-1.5">
                <Input
                  label="Số kết quả muốn xem"
                  type="number"
                  min="1"
                  max="100"
                  value={request.topK}
                  onChange={(event) => update("topK", event.target.value)}
                />
                <p className="text-xs text-slate-500 m-0">
                  AI sẽ hiển thị các kết quả có điểm liên kết cao nhất.
                </p>
              </div>
            )}

            <label className="flex items-start gap-3 p-3 rounded-[var(--radius-md)] border border-emerald-200/60 bg-emerald-50/40 cursor-pointer hover:bg-emerald-50/70 transition-colors">
              <input
                type="checkbox"
                checked={request.medicalWarningAccepted}
                onChange={(event) =>
                  update("medicalWarningAccepted", event.target.checked)
                }
                className="w-5 h-5 mt-0.5 accent-teal-600 shrink-0"
              />
              <span className="text-sm text-emerald-800 leading-relaxed">
                Kết quả chỉ phục vụ học tập, nghiên cứu và tham khảo, không
                thay thế tư vấn của bác sĩ hoặc dược sĩ.
              </span>
            </label>

            {error && (
              <div ref={errorRef}>
                <Alert tone="danger">{error}</Alert>
              </div>
            )}

            <div className="flex justify-end pt-1">
              <Button
                className="w-full sm:w-auto !h-11 px-5 shadow-[0_12px_26px_rgba(20,184,166,0.18)]"
                loading={submitting}
                disabled={submitting}
              >
                {submitting ? <Brain size={18} /> : <Sparkles size={18} />}
                {submitting ? "Đang phân tích..." : meta.actionLabel}
              </Button>
            </div>
          </form>
        </Card>

        <div className="space-y-4">
          <Card>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              AI đang làm gì?
            </span>
            <h3 className="text-base font-bold text-slate-900 m-0 mb-3">
              RandomForest chấm điểm liên kết thuốc-bệnh
            </h3>
            <p className="text-sm text-slate-600 m-0 leading-relaxed mb-4">
              {assistantNote}
            </p>

            <div className="grid gap-2">
              {AI_EXPLANATIONS.map((item) => (
                <div
                  key={item.title}
                  className="rounded-xl border border-blue-100 bg-blue-50/40 px-3 py-2.5"
                >
                  <strong className="block text-sm text-slate-800">
                    {item.title}
                  </strong>
                  <span className="text-xs leading-relaxed text-slate-500">
                    {item.body}
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-4 flex items-start gap-2 rounded-xl border border-amber-200/70 bg-amber-50/80 p-3 text-xs leading-relaxed text-amber-800">
              <ShieldAlert size={15} className="mt-0.5 shrink-0" />
              <span>
                Kết quả chỉ phục vụ học tập, nghiên cứu và tham khảo, không
                thay thế tư vấn của bác sĩ hoặc dược sĩ.
              </span>
            </div>
          </Card>

          <MedicalWarning />

          <Card className="!p-4">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-2">
              Trạng thái hệ thống
            </span>
            <div className="flex flex-wrap gap-1.5">
              <SystemStatusBadge type="backend" status={backendStatus} />
              <SystemStatusBadge type="database" status={databaseStatus} />
              <SystemStatusBadge type="ai" status={aiStatus} />
            </div>
            <div className="mt-4 grid gap-2 text-xs">
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 font-semibold text-slate-500">
                  <Pill size={14} className="text-teal-500" />
                  Thuốc
                </span>
                <strong className="text-slate-800">
                  {drugs.loading ? "Đang tải" : drugItems.length}
                </strong>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 font-semibold text-slate-500">
                  <Stethoscope size={14} className="text-cyan-500" />
                  Bệnh/chỉ định
                </span>
                <strong className="text-slate-800">
                  {diseases.loading ? "Đang tải" : diseaseItems.length}
                </strong>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2">
                <span className="flex items-center gap-2 font-semibold text-slate-500">
                  <CheckCircle2 size={14} className="text-emerald-500" />
                  Mode hiện tại
                </span>
                <strong className="text-slate-800">{meta.shortLabel}</strong>
              </div>
            </div>
          </Card>
        </div>
      </div>

      <div ref={resultsRef} className="scroll-mt-28 lg:scroll-mt-40">
        <Card>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
            <div>
              <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
                AI RESULT
              </span>
              <h2 className="text-lg font-bold text-slate-900 m-0">
                {response ? resultMeta.resultTitle : "Kết quả AI"}
              </h2>
              <p className="text-sm text-slate-500 mt-1 m-0">
                {submitting
                  ? "Hệ thống đang chấm điểm liên kết bằng AI."
                  : response
                    ? resultMode === "PAIR_CHECK"
                      ? "Frontend chỉ hiển thị result đầu tiên như một panel kết luận cho cặp cụ thể."
                      : `Tìm thấy ${results.length} kết quả và xếp hạng theo điểm AI.`
                    : "Kết quả sẽ hiển thị sau khi bạn gửi yêu cầu dự đoán."}
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
                Đang chấm điểm khả năng tồn tại liên kết thuốc-bệnh...
              </Alert>
              <LoadingSkeleton count={3} variant="row" />
            </div>
          ) : apiError ? (
            <Alert tone="danger">{apiError}</Alert>
          ) : !response ? (
            <EmptyState icon={Sparkles} title="Chưa có kết quả">
              Chọn mode dự đoán, dữ liệu đầu vào và xác nhận cảnh báo y khoa để
              xem kết quả AI.
            </EmptyState>
          ) : results.length === 0 ? (
            <EmptyState icon={Sparkles} title={resultMeta.emptyTitle}>
              Backend chưa trả về kết quả phù hợp cho yêu cầu hiện tại.
            </EmptyState>
          ) : resultMode === "PAIR_CHECK" ? (
            <PairCheckResultPanel
              result={results[0]}
              drugImage={drugImageById.get(String(results[0]?.thuocId || results[0]?.drugId))}
            />
          ) : (
            <div ref={resultRevealRef} className="space-y-3">
              {results.map((result, index) => (
                <PredictionResultCard
                  key={result.ketQuaDuDoanId || result.predictionResultId || index}
                  result={result}
                  index={index}
                  mode={resultMode}
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
