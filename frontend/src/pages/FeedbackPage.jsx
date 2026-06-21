import {
  AlertTriangle,
  CheckCircle2,
  MessageSquare,
  Send,
  Star,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import toast from "react-hot-toast";
import { api } from "../api";
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
import { useLoad } from "../hooks/useLoad";
import { getItems, normalizeApiError } from "../utils/format";

/* ── Assessment options ── */
const ASSESSMENT_OPTIONS = [
  { value: "Hợp lý", label: "Hợp lý", tone: "emerald", icon: CheckCircle2 },
  { value: "Cần kiểm tra thêm", label: "Cần kiểm tra thêm", tone: "amber", icon: AlertTriangle },
  { value: "Không phù hợp", label: "Không phù hợp", tone: "red", icon: XCircle },
];

/* ── Issue types per spec ── */
const ISSUE_TYPES = [
  "Giữ kết quả",
  "Kết quả không phù hợp",
  "Thiếu dữ liệu",
  "Điểm tin cậy chưa hợp lý",
  "Lỗi giao diện",
  "Khác",
];

const STAR_LABELS = ["", "Rất tệ", "Tệ", "Trung bình", "Tốt", "Rất tốt"];

export function FeedbackPage({ user }) {
  const history = useLoad(() => api.getPredictionHistory(), []);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState({
    predictionResultId: "",
    generalAssessment: "Hợp lý",
    usefulScore: 5,
    suggestedAction: "Giữ kết quả",
    reasonText: "",
  });
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const historyItems = getItems(history.data);

  useEffect(() => {
    if (!selectedRunId) {
      setDetail(null);
      return;
    }

    let active = true;
    setLoadingDetail(true);
    api
      .getPrediction(selectedRunId)
      .then((data) => {
        if (active) {
          setDetail(data);
          const firstResult = data.results?.[0];
          setForm((current) => ({
            ...current,
            predictionResultId:
              firstResult?.ketQuaDuDoanId ||
              firstResult?.predictionResultId ||
              "",
          }));
        }
      })
      .catch((err) => active && setError(normalizeApiError(err.message)))
      .finally(() => active && setLoadingDetail(false));

    return () => {
      active = false;
    };
  }, [selectedRunId]);

  function update(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitted(false);

    if (!selectedRunId) {
      const msg = "Vui lòng chọn yêu cầu dự đoán.";
      setError(msg);
      toast.error(msg);
      return;
    }

    setSubmitting(true);
    try {
      await api.createFeedback({
        predictionRunId: Number(selectedRunId),
        predictionResultId: form.predictionResultId
          ? Number(form.predictionResultId)
          : null,
        userId: user?.userId || user?.nguoiDungId || null,
        generalAssessment: form.generalAssessment,
        usefulScore: Number(form.usefulScore),
        suggestedAction: form.suggestedAction,
        reasonText: form.reasonText.trim() || null,
      });

      toast.success("Đã gửi phản hồi. Cảm ơn bạn đã giúp cải thiện hệ thống!");
      setSubmitted(true);
      setForm({
        predictionResultId: "",
        generalAssessment: "Hợp lý",
        usefulScore: 5,
        suggestedAction: "Giữ kết quả",
        reasonText: "",
      });
      setSelectedRunId("");
      setDetail(null);
    } catch (err) {
      const msg = normalizeApiError(err.message);
      setError(msg);
      toast.error(msg);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="space-y-5">
      <div className="grid grid-cols-1 lg:grid-cols-[1.3fr,0.7fr] gap-5 items-start">
        {/* Left: Feedback Form */}
        <Card>
          <div className="mb-5">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              Feedback form
            </span>
            <h3 className="text-lg font-bold text-slate-900 m-0">
              Gửi phản hồi kết quả
            </h3>
            <p className="text-sm text-slate-500 mt-1 m-0">
              Nhận xét giúp cải thiện chất lượng dự đoán và dữ liệu liên kết.
            </p>
          </div>

          {/* Success banner */}
          {submitted && (
            <div className="flex items-center gap-3 p-4 rounded-[var(--radius-md)] bg-emerald-50 border border-emerald-200/60 mb-4">
              <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-emerald-800 m-0">
                  Phản hồi đã được ghi nhận!
                </p>
                <p className="text-xs text-emerald-700 m-0 mt-0.5">
                  Cảm ơn bạn đã đóng góp để cải thiện hệ thống.
                </p>
              </div>
            </div>
          )}

          {history.loading ? (
            <LoadingSkeleton count={2} variant="row" />
          ) : historyItems.length === 0 ? (
            <EmptyState icon={MessageSquare} title="Chưa có lịch sử dự đoán">
              Bạn cần tạo ít nhất một yêu cầu dự đoán trước khi gửi phản hồi.
            </EmptyState>
          ) : (
            <form className="space-y-4" onSubmit={submit}>
              {/* Select prediction request */}
              <Select
                label="Yêu cầu dự đoán"
                value={selectedRunId}
                onChange={(e) => {
                  setSelectedRunId(e.target.value);
                  setSubmitted(false);
                  setError("");
                }}
              >
                <option value="">Chọn yêu cầu dự đoán</option>
                {historyItems.map((item) => {
                  const id = item.yeuCauDuDoanId || item.requestId;
                  return (
                    <option key={id} value={id}>
                      {item.maYeuCau || item.requestCode} –{" "}
                      {item.kieuDuDoan || item.predictionType}
                    </option>
                  );
                })}
              </Select>

              {/* Select specific result */}
              <Select
                label="Kết quả cần phản hồi"
                value={form.predictionResultId}
                onChange={(e) => update("predictionResultId", e.target.value)}
              >
                <option value="">Toàn bộ yêu cầu</option>
                {(detail?.results ?? []).map((item) => (
                  <option
                    key={item.ketQuaDuDoanId || item.predictionResultId}
                    value={item.ketQuaDuDoanId || item.predictionResultId}
                  >
                    #{item.thuHang || item.rankNo}{" "}
                    {item.tenThuoc || item.drugName} –{" "}
                    {item.tenBenh || item.diseaseName}
                  </option>
                ))}
              </Select>

              {/* Assessment */}
              <div>
                <span className="block text-sm font-semibold text-slate-700 mb-2">
                  Đánh giá tổng quan
                </span>
                <div className="flex flex-wrap gap-2">
                  {ASSESSMENT_OPTIONS.map((opt) => (
                    (() => {
                      const OptionIcon = opt.icon;
                      return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => update("generalAssessment", opt.value)}
                      className={`px-3.5 py-2 rounded-[var(--radius-md)] text-sm font-semibold border transition-all duration-200 flex items-center gap-1.5 ${
                        form.generalAssessment === opt.value
                          ? opt.tone === "emerald"
                            ? "border-emerald-300 bg-emerald-50 text-emerald-700 shadow-sm"
                            : opt.tone === "amber"
                              ? "border-amber-300 bg-amber-50 text-amber-700 shadow-sm"
                              : "border-red-300 bg-red-50 text-red-700 shadow-sm"
                          : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
                        }`}
                    >
                      <OptionIcon size={15} />
                      {opt.label}
                    </button>
                      );
                    })()
                  ))}
                </div>
              </div>

              {/* Star rating */}
              <div>
                <span className="block text-sm font-semibold text-slate-700 mb-2">
                  Mức độ hữu ích (1–5){" "}
                  {form.usefulScore > 0 && (
                    <span className="text-xs text-slate-400 font-normal ml-1">
                      — {STAR_LABELS[form.usefulScore]}
                    </span>
                  )}
                </span>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      type="button"
                      onClick={() => update("usefulScore", n)}
                      className={`star-btn w-11 h-11 rounded-xl flex items-center justify-center border transition-all duration-200 ${
                        form.usefulScore >= n
                          ? "border-amber-300 bg-amber-50 text-amber-500 shadow-sm"
                          : "border-slate-200 bg-white text-slate-300 hover:text-slate-400"
                      }`}
                      title={STAR_LABELS[n]}
                    >
                      <Star
                        size={20}
                        fill={form.usefulScore >= n ? "currentColor" : "none"}
                      />
                    </button>
                  ))}
                </div>
              </div>

              {/* Issue type */}
              <Select
                label="Loại vấn đề / đề xuất hành động"
                value={form.suggestedAction}
                onChange={(e) => update("suggestedAction", e.target.value)}
              >
                {ISSUE_TYPES.map((t) => (
                  <option key={t}>{t}</option>
                ))}
              </Select>

              {/* Reason text */}
              <Input
                label="Lý do / góp ý chi tiết"
                textarea
                value={form.reasonText}
                onChange={(e) => update("reasonText", e.target.value)}
                placeholder="Nhập nhận xét của bạn về kết quả dự đoán..."
              />

              {/* Error */}
              {error && <Alert tone="danger">{error}</Alert>}

              {/* Submit */}
              <Button
                className="w-full !h-12"
                loading={submitting}
                disabled={submitting}
              >
                <Send size={16} />
                {submitting ? "Đang gửi..." : "Gửi phản hồi"}
              </Button>
            </form>
          )}
        </Card>

        {/* Right: Preview panel */}
        <Card>
          <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-3">
            Thông tin yêu cầu đã chọn
          </span>

          {history.loading || loadingDetail ? (
            <LoadingSkeleton count={2} variant="row" />
          ) : !selectedRunId ? (
            <EmptyState icon={MessageSquare} title="Chưa chọn yêu cầu">
              Chọn một yêu cầu dự đoán để xem thông tin có thể phản hồi.
            </EmptyState>
          ) : detail ? (
            <div className="space-y-4">
              {/* Request info */}
              <div className="p-3 rounded-[var(--radius-md)] bg-slate-50 border border-slate-100">
                <h4 className="text-sm font-bold text-slate-800 m-0">
                  {detail.maYeuCau || detail.requestCode}
                </h4>
                {detail.resultMessage && (
                  <p className="text-xs text-slate-500 mt-1 m-0 leading-relaxed">
                    {detail.resultMessage}
                  </p>
                )}
                <div className="flex items-center gap-2 mt-2 flex-wrap">
                  <Badge tone="cyan">
                    {detail.kieuDuDoan || detail.predictionType}
                  </Badge>
                  <Badge tone="slate">
                    {detail.results?.length ?? 0} kết quả
                  </Badge>
                  {(detail.nguonDiem || detail.scoreSource) && (
                    <Badge
                      tone={
                        (detail.nguonDiem || detail.scoreSource) ===
                        "DATABASE_FALLBACK"
                          ? "amber"
                          : "emerald"
                      }
                    >
                      {detail.nguonDiem || detail.scoreSource}
                    </Badge>
                  )}
                </div>
              </div>

              {/* Results list */}
              {(detail.results ?? []).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
                    Kết quả dự đoán
                  </h4>
                  {detail.results.map((r) => {
                    const rId =
                      r.ketQuaDuDoanId || r.predictionResultId;
                    const isSelected =
                      String(form.predictionResultId) === String(rId);
                    return (
                      <div
                        key={rId}
                        className={`p-2.5 rounded-lg border text-xs transition-colors ${
                          isSelected
                            ? "border-teal-200 bg-teal-50/50"
                            : "border-slate-100 bg-white"
                        }`}
                      >
                        <strong className="text-slate-800">
                          #{r.thuHang || r.rankNo}
                        </strong>{" "}
                        <span className="text-slate-600">
                          {r.tenThuoc || r.drugName} →{" "}
                          {r.tenBenh || r.diseaseName}
                        </span>
                        {(r.diemDuDoan ?? r.predictionScore) != null && (
                          <span className="ml-2 font-bold text-teal-600">
                            {Number(r.diemDuDoan ?? r.predictionScore).toFixed(4)}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : null}
        </Card>
      </div>
    </section>
  );
}
