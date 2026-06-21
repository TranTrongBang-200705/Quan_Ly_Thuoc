import {
  AlertTriangle,
  Calendar,
  CheckCircle2,
  MessageSquare,
  Search,
  Send,
  Star,
  UserRound,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
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
import { formatDateTime, getItems, normalizeApiError } from "../utils/format";

const ASSESSMENT_OPTIONS = [
  { value: "Hợp lý", label: "Hợp lý", tone: "emerald", icon: CheckCircle2 },
  { value: "Cần kiểm tra thêm", label: "Cần kiểm tra thêm", tone: "amber", icon: AlertTriangle },
  { value: "Không phù hợp", label: "Không phù hợp", tone: "red", icon: XCircle },
];

const STAR_LABELS = ["", "Rất tệ", "Tệ", "Trung bình", "Tốt", "Rất tốt"];
const ADMIN_API_MISSING_MESSAGE = "Backend chưa cung cấp API danh sách phản hồi cho admin.";

function pickValue(...values) {
  return values.find((value) => value !== null && value !== undefined && String(value).trim() !== "") ?? "";
}

function normalizeAssessment(value) {
  const text = String(value || "").trim();
  const lower = text.toLowerCase();

  if (!text) return "";
  if (lower.includes("không") || lower.includes("chưa hợp") || lower.includes("not")) {
    return "Không phù hợp";
  }
  if (lower.includes("kiểm") || lower.includes("chứng") || lower.includes("need")) {
    return "Cần kiểm tra thêm";
  }
  if (lower.includes("hợp") || lower.includes("useful")) return "Hợp lý";
  return text;
}

function assessmentTone(value) {
  const normalized = normalizeAssessment(value);
  if (normalized === "Hợp lý") return "emerald";
  if (normalized === "Cần kiểm tra thêm") return "amber";
  if (normalized === "Không phù hợp") return "red";
  return "slate";
}

function roleName(role) {
  if (typeof role === "string") return role;
  return role?.roleCode || role?.code || role?.name || role?.role || "";
}

function hasAdminRole({ user, roles, isAdmin }) {
  if (isAdmin) return true;
  const roleValues = roles?.length ? roles : user?.roles ?? [];
  return roleValues.some((role) => String(roleName(role)).toUpperCase() === "ADMIN");
}

function resultLabelFrom(item, result) {
  const drug = pickValue(item.tenThuoc, item.drugName, result.tenThuoc, result.drugName);
  const disease = pickValue(item.tenBenh, item.diseaseName, result.tenBenh, result.diseaseName);
  if (drug && disease) return `${drug} → ${disease}`;
  return pickValue(
    item.resultLabel,
    item.ketQuaDuocPhanHoi,
    item.predictionResult,
    item.tenKetQua,
    result.resultLabel,
    result.tenKetQua,
    drug,
    disease,
  );
}

function normalizeFeedbackItem(item) {
  const user = item.user || item.nguoiDung || item.sender || item.createdBy || {};
  const result = item.result || item.ketQua || item.ketQuaDuDoan || {};
  const request =
    item.request ||
    item.yeuCau ||
    item.yeuCauDuDoan ||
    item.predictionRun ||
    item.run ||
    result.yeuCauDuDoan ||
    {};

  return {
    code: pickValue(item.maPhanHoi, item.feedbackCode, item.phanHoiId, item.feedbackId, item.id),
    senderName: pickValue(
      item.senderName,
      item.userName,
      item.username,
      item.fullName,
      item.nguoiGui,
      user.fullName,
      user.hoTen,
      user.displayName,
      user.username,
      user.email,
    ),
    senderIdentity: pickValue(
      item.senderEmail,
      item.email,
      item.userEmail,
      item.username,
      user.email,
      user.username,
    ),
    requestCode: pickValue(
      item.maYeuCau,
      item.requestCode,
      item.predictionRequestCode,
      request.maYeuCau,
      request.requestCode,
      request.yeuCauDuDoanId,
      request.requestId,
    ),
    predictionType: pickValue(
      item.kieuDuDoan,
      item.predictionType,
      request.kieuDuDoan,
      request.predictionType,
    ),
    resultLabel: resultLabelFrom(item, result),
    assessment: normalizeAssessment(
      pickValue(item.generalAssessment, item.danhGia, item.assessment, item.danh_gia),
    ),
    usefulScore: pickValue(item.usefulScore, item.mucDoHuuIch, item.score, item.rating),
    comment: pickValue(
      item.reasonText,
      item.nhanXet,
      item.comment,
      item.noiDungGopY,
      item.feedbackText,
      item.note,
    ),
    createdAt: pickValue(item.createdAt, item.ngayTao, item.submittedAt, item.created_at),
    status: pickValue(item.trangThaiXuLy, item.status, item.processingStatus),
  };
}

function missingAdminFeedbackApi(error) {
  const text = String(error || "").toLowerCase();
  return text.includes("404") || text.includes("not found") || text.includes("/admin/feedbacks");
}

export function FeedbackPage({ user, roles = [], isAdmin = false }) {
  if (hasAdminRole({ user, roles, isAdmin })) {
    return <AdminFeedbackList />;
  }

  return <UserFeedbackForm user={user} />;
}

function UserFeedbackForm({ user }) {
  const history = useLoad(() => api.getPredictionHistory(), []);
  const [selectedRunId, setSelectedRunId] = useState("");
  const [detail, setDetail] = useState(null);
  const [form, setForm] = useState({
    predictionResultId: "",
    generalAssessment: "Hợp lý",
    usefulScore: 5,
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
      return undefined;
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
        suggestedAction: null,
        reasonText: form.reasonText.trim() || null,
      });

      toast.success("Đã gửi phản hồi. Cảm ơn bạn đã giúp cải thiện hệ thống.");
      setSubmitted(true);
      setForm({
        predictionResultId: "",
        generalAssessment: "Hợp lý",
        usefulScore: 5,
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

          {submitted && (
            <div className="flex items-center gap-3 p-4 rounded-[var(--radius-md)] bg-emerald-50 border border-emerald-200/60 mb-4">
              <CheckCircle2 size={20} className="text-emerald-600 shrink-0" />
              <div>
                <p className="text-sm font-semibold text-emerald-800 m-0">
                  Phản hồi đã được ghi nhận.
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
                      {item.maYeuCau || item.requestCode} - {item.kieuDuDoan || item.predictionType}
                    </option>
                  );
                })}
              </Select>

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
                    #{item.thuHang || item.rankNo} {item.tenThuoc || item.drugName} -{" "}
                    {item.tenBenh || item.diseaseName}
                  </option>
                ))}
              </Select>

              <div>
                <span className="block text-sm font-semibold text-slate-700 mb-2">
                  Đánh giá tổng quan
                </span>
                <div className="flex flex-wrap gap-2">
                  {ASSESSMENT_OPTIONS.map((opt) => {
                    const OptionIcon = opt.icon;
                    const active = form.generalAssessment === opt.value;
                    return (
                      <button
                        key={opt.value}
                        type="button"
                        onClick={() => update("generalAssessment", opt.value)}
                        className={`px-3.5 py-2 rounded-[var(--radius-md)] text-sm font-semibold border transition-all duration-200 flex items-center gap-1.5 ${
                          active
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
                  })}
                </div>
              </div>

              <div>
                <span className="block text-sm font-semibold text-slate-700 mb-2">
                  Mức độ hữu ích (1-5){" "}
                  {form.usefulScore > 0 && (
                    <span className="text-xs text-slate-400 font-normal ml-1">
                      - {STAR_LABELS[form.usefulScore]}
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

              <Input
                label="Nội dung góp ý"
                textarea
                value={form.reasonText}
                onChange={(e) => update("reasonText", e.target.value)}
                placeholder="Nhập nhận xét của bạn về kết quả dự đoán..."
              />

              {error && <Alert tone="danger">{error}</Alert>}

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
                        (detail.nguonDiem || detail.scoreSource) === "DATABASE_FALLBACK"
                          ? "amber"
                          : "emerald"
                      }
                    >
                      {detail.nguonDiem || detail.scoreSource}
                    </Badge>
                  )}
                </div>
              </div>

              {(detail.results ?? []).length > 0 && (
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wide m-0">
                    Kết quả dự đoán
                  </h4>
                  {detail.results.map((r) => {
                    const rId = r.ketQuaDuDoanId || r.predictionResultId;
                    const isSelected = String(form.predictionResultId) === String(rId);
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
                          {r.tenThuoc || r.drugName} → {r.tenBenh || r.diseaseName}
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

function AdminFeedbackList() {
  const feedback = useLoad(() => api.getAdminFeedbacks(), []);
  const [assessmentFilter, setAssessmentFilter] = useState("Tất cả");
  const [keyword, setKeyword] = useState("");

  const items = useMemo(
    () => getItems(feedback.data).map(normalizeFeedbackItem),
    [feedback.data],
  );

  const filteredItems = useMemo(() => {
    const normalizedKeyword = keyword.trim().toLowerCase();
    return items.filter((item) => {
      const matchesAssessment =
        assessmentFilter === "Tất cả" || normalizeAssessment(item.assessment) === assessmentFilter;

      if (!matchesAssessment) return false;
      if (!normalizedKeyword) return true;

      return [
        item.code,
        item.senderName,
        item.senderIdentity,
        item.requestCode,
        item.predictionType,
        item.resultLabel,
        item.comment,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedKeyword);
    });
  }, [assessmentFilter, items, keyword]);

  const apiMissing = feedback.error && missingAdminFeedbackApi(feedback.error);

  return (
    <section className="space-y-5">
      <Card>
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              Feedback management
            </span>
            <h3 className="text-lg font-bold text-slate-900 m-0">
              Danh sách phản hồi người dùng
            </h3>
            <p className="text-sm text-slate-500 mt-1 m-0">
              Lọc theo đánh giá và tìm kiếm theo mã yêu cầu, tài khoản hoặc nội dung góp ý.
            </p>
          </div>

          <div className="grid w-full gap-3 lg:w-[460px] sm:grid-cols-[1fr,180px]">
            <Input
              label="Tìm kiếm"
              icon={Search}
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              placeholder="Mã yêu cầu, email, nội dung..."
            />
            <Select
              label="Bộ lọc"
              value={assessmentFilter}
              onChange={(event) => setAssessmentFilter(event.target.value)}
            >
              {["Tất cả", ...ASSESSMENT_OPTIONS.map((item) => item.value)].map((value) => (
                <option key={value}>{value}</option>
              ))}
            </Select>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          {["Tất cả", ...ASSESSMENT_OPTIONS.map((item) => item.value)].map((value) => (
            <button
              key={value}
              type="button"
              onClick={() => setAssessmentFilter(value)}
              className={`rounded-full border px-3 py-1.5 text-xs font-bold transition-colors ${
                assessmentFilter === value
                  ? "border-teal-300 bg-teal-50 text-teal-700"
                  : "border-slate-200 bg-white text-slate-500 hover:bg-slate-50"
              }`}
            >
              {value}
            </button>
          ))}
        </div>
      </Card>

      {feedback.loading ? (
        <LoadingSkeleton count={3} variant="row" />
      ) : apiMissing ? (
        <Alert tone="warning">{ADMIN_API_MISSING_MESSAGE}</Alert>
      ) : feedback.error ? (
        <Alert tone="danger">
          Không thể tải danh sách phản hồi. {feedback.error}
        </Alert>
      ) : filteredItems.length === 0 ? (
        <EmptyState icon={MessageSquare} title="Chưa có phản hồi nào từ người dùng.">
          Khi người dùng gửi đánh giá kết quả dự đoán, danh sách sẽ hiển thị tại đây.
        </EmptyState>
      ) : (
        <div className="grid gap-3">
          {filteredItems.map((item, index) => (
            <Card key={`${item.code || item.requestCode || "feedback"}-${index}`} className="!p-4">
              <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge tone="teal">
                      {item.code ? `Mã phản hồi: ${item.code}` : "Phản hồi"}
                    </Badge>
                    {item.assessment && (
                      <Badge tone={assessmentTone(item.assessment)}>
                        {normalizeAssessment(item.assessment)}
                      </Badge>
                    )}
                    {item.status && <Badge tone="slate">{item.status}</Badge>}
                  </div>

                  <h4 className="mt-3 mb-0 text-base font-bold text-slate-900">
                    {item.resultLabel || "Kết quả dự đoán"}
                  </h4>
                  <p className="mt-1 mb-0 text-sm leading-relaxed text-slate-600">
                    {item.comment || "Người dùng chưa nhập nội dung góp ý."}
                  </p>
                </div>

                <div className="flex shrink-0 flex-wrap gap-2 text-xs text-slate-500 lg:justify-end">
                  {item.createdAt && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-50 px-2.5 py-1 font-semibold">
                      <Calendar size={13} />
                      {formatDateTime(item.createdAt)}
                    </span>
                  )}
                  {item.usefulScore && (
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-2.5 py-1 font-bold text-amber-700">
                      <Star size={13} fill="currentColor" />
                      {item.usefulScore}/5
                    </span>
                  )}
                </div>
              </div>

              <div className="mt-4 grid gap-3 border-t border-slate-100 pt-3 sm:grid-cols-2 lg:grid-cols-4">
                <FeedbackMeta icon={UserRound} label="Người gửi" value={item.senderName || "Chưa rõ"} />
                <FeedbackMeta label="Email/username" value={item.senderIdentity || "-"} />
                <FeedbackMeta label="Mã yêu cầu" value={item.requestCode || "-"} />
                <FeedbackMeta label="Loại dự đoán" value={item.predictionType || "-"} />
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}

function FeedbackMeta({ icon: Icon, label, value }) {
  return (
    <div className="min-w-0 rounded-xl border border-slate-100 bg-slate-50/70 px-3 py-2">
      <span className="mb-1 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wide text-slate-400">
        {Icon && <Icon size={13} />}
        {label}
      </span>
      <strong className="block truncate text-sm text-slate-800">{value}</strong>
    </div>
  );
}
