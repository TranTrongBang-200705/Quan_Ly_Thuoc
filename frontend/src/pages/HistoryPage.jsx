import { Clock, Eye, Filter, History, Pill, Stethoscope, X } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "../api";
import { PredictionResultCard } from "../components/medical";
import {
  Alert,
  Badge,
  Button,
  Card,
  EmptyState,
  LoadingSkeleton,
  Select,
} from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { formatDateTime, getItems, normalizeApiError } from "../utils/format";

/* ── Friendly prediction type labels ── */
const TYPE_LABEL = {
  DRUG_TO_DISEASE: "Thuốc → Bệnh",
  DISEASE_TO_DRUG: "Bệnh → Thuốc",
  PAIR_CHECK: "Kiểm tra cặp",
  PAIR_PREDICTION: "Kiểm tra cặp",
};

function typeBadgeTone(type) {
  if (type === "DRUG_TO_DISEASE") return "cyan";
  if (type === "DISEASE_TO_DRUG") return "blue";
  return "slate";
}

function statusBadgeTone(status) {
  const s = String(status || "").toLowerCase();
  if (s.includes("hoàn") || s.includes("complet") || s.includes("success"))
    return "emerald";
  if (s.includes("đang") || s.includes("pending") || s.includes("process"))
    return "amber";
  if (s.includes("lỗi") || s.includes("fail") || s.includes("error"))
    return "red";
  return "slate";
}

const PREDICTION_TYPE_OPTIONS = [
  { value: "", label: "Tất cả loại" },
  { value: "DRUG_TO_DISEASE", label: "Thuốc → Bệnh" },
  { value: "DISEASE_TO_DRUG", label: "Bệnh → Thuốc" },
  { value: "PAIR_CHECK", label: "Kiểm tra cặp" },
];

export function HistoryPage({ admin = false }) {
  const history = useLoad(
    () =>
      admin
        ? api.getAdminPredictionHistory({})
        : api.getPredictionHistory(),
    [admin]
  );

  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState("");
  const [loadingDetail, setLoadingDetail] = useState(false);

  /* Client-side filters */
  const [filterType, setFilterType] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  const allItems = getItems(history.data);

  const items = useMemo(() => {
    return allItems.filter((item) => {
      const type = item.kieuDuDoan || item.predictionType || "";
      const status = item.trangThaiYeuCau || item.requestStatus || "";

      const matchType = filterType ? type === filterType : true;
      const matchStatus = filterStatus
        ? status.toLowerCase().includes(filterStatus.toLowerCase())
        : true;

      return matchType && matchStatus;
    });
  }, [allItems, filterType, filterStatus]);

  /* Unique status values for filter */
  const statusOptions = useMemo(() => {
    const set = new Set(
      allItems.map((i) => i.trangThaiYeuCau || i.requestStatus).filter(Boolean)
    );
    return Array.from(set);
  }, [allItems]);

  async function openDetail(id) {
    setDetailError("");
    setLoadingDetail(true);
    try {
      setDetail(await api.getPrediction(id));
    } catch (err) {
      setDetailError(normalizeApiError(err.message));
    } finally {
      setLoadingDetail(false);
    }
  }

  const hasFilters = filterType || filterStatus;

  return (
    <section className="space-y-5">
      {history.error && (
        <Alert tone="danger">
          Không thể tải lịch sử dự đoán. Vui lòng kiểm tra kết nối Backend hoặc thử lại.
        </Alert>
      )}

      {/* Filters */}
      {!history.loading && allItems.length > 0 && (
        <Card className="!p-4">
          <div className="flex flex-col sm:flex-row gap-3 items-end">
            <Select
              label="Loại dự đoán"
              icon={Filter}
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              {PREDICTION_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </Select>

            <Select
              label="Trạng thái"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="">Tất cả trạng thái</option>
              {statusOptions.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>

            {hasFilters && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setFilterType("");
                  setFilterStatus("");
                }}
                className="shrink-0"
              >
                <X size={14} />
                Xóa bộ lọc
              </Button>
            )}
          </div>
        </Card>
      )}

      {history.loading ? (
        <LoadingSkeleton count={5} variant="row" />
      ) : allItems.length === 0 ? (
        <EmptyState icon={History} title="Chưa có lịch sử dự đoán">
          Tạo yêu cầu dự đoán để lưu lại hoạt động tại đây.
        </EmptyState>
      ) : items.length === 0 ? (
        <EmptyState icon={Filter} title="Không có yêu cầu phù hợp">
          Không có dữ liệu phù hợp với bộ lọc hiện tại. Thử thay đổi loại dự
          đoán hoặc trạng thái.
        </EmptyState>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-[1.3fr,0.7fr] gap-5 items-start">
          {/* Left: Timeline */}
          <Card>
            <div className="mb-3">
              <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
                Audit trail
              </span>
              <h3 className="text-base font-bold text-slate-900 m-0">
                Danh sách yêu cầu{" "}
                <span className="text-slate-400 font-normal text-sm">
                  ({items.length})
                </span>
              </h3>
            </div>

            <div className="space-y-2">
              {items.map((item) => {
                const id =
                  item.yeuCauDuDoanId ||
                  item.requestId ||
                  item.predictionRunId;
                const isActive =
                  detail &&
                  (detail.yeuCauDuDoanId === id || detail.requestId === id);
                const type = item.kieuDuDoan || item.predictionType;
                const status =
                  item.trangThaiYeuCau || item.requestStatus || "Hoàn thành";
                const drugName = item.tenThuoc || item.drugName;
                const diseaseName = item.tenBenh || item.diseaseName;

                return (
                  <button
                    key={id}
                    onClick={() => openDetail(id)}
                    className={`w-full flex items-start gap-3 p-3.5 rounded-[var(--radius-md)] border text-left transition-all duration-200 cursor-pointer ${
                      isActive
                        ? "border-teal-200 bg-teal-50/50 shadow-sm"
                        : "border-slate-100 bg-white hover:bg-slate-50 hover:border-slate-200"
                    }`}
                  >
                    {/* Timeline dot */}
                    <div className="w-9 h-9 rounded-full bg-blue-50 text-blue-500 flex items-center justify-center shrink-0 mt-0.5">
                      <Clock size={15} />
                    </div>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <strong className="text-sm text-slate-800 truncate">
                          {item.maYeuCau || item.requestCode || `#${id}`}
                        </strong>
                        <Badge
                          tone={typeBadgeTone(type)}
                          className="shrink-0"
                        >
                          {TYPE_LABEL[type] || type || "Dự đoán"}
                        </Badge>
                        <Badge
                          tone={statusBadgeTone(status)}
                          className="shrink-0"
                        >
                          {status}
                        </Badge>
                      </div>

                      {/* Drug / Disease input info */}
                      {(drugName || diseaseName) && (
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mb-0.5">
                          {drugName && (
                            <span className="inline-flex min-w-0 items-center gap-1">
                              <Pill size={12} className="shrink-0 text-teal-500" />
                              <span className="truncate">{drugName}</span>
                            </span>
                          )}
                          {diseaseName && (
                            <span className="inline-flex min-w-0 items-center gap-1">
                              <Stethoscope size={12} className="shrink-0 text-cyan-500" />
                              <span className="truncate">{diseaseName}</span>
                            </span>
                          )}
                        </div>
                      )}

                      <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                        <span>
                          {formatDateTime(item.ngayTao || item.createdAt)}
                        </span>
                        <span>•</span>
                        <span>
                          {item.soKetQua ?? item.resultCount ?? 0} kết quả
                        </span>
                        {item.nguongDiem != null && (
                          <>
                            <span>•</span>
                            <span>
                              Ngưỡng {item.nguongDiem ?? item.scoreThreshold}
                            </span>
                          </>
                        )}
                        {item.soKetQuaToiDa != null && (
                          <>
                            <span>•</span>
                            <span>
                              Top {item.soKetQuaToiDa ?? item.topK}
                            </span>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Eye icon */}
                    <Eye
                      size={16}
                      className={`shrink-0 mt-1 transition-colors ${
                        isActive ? "text-teal-400" : "text-slate-300"
                      }`}
                    />
                  </button>
                );
              })}
            </div>
          </Card>

          {/* Right: Detail panel */}
          <Card>
            <div className="flex items-center justify-between mb-3">
              <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase">
                Chi tiết yêu cầu
              </span>
              {detail && (
                <button
                  onClick={() => setDetail(null)}
                  className="w-7 h-7 rounded-lg hover:bg-slate-100 flex items-center justify-center border-0 bg-transparent transition-colors"
                  aria-label="Đóng chi tiết"
                >
                  <X size={16} className="text-slate-400" />
                </button>
              )}
            </div>

            {!detail && !loadingDetail && (
              <EmptyState title="Chọn một yêu cầu">
                Nhấn vào yêu cầu bên trái để xem lại kết quả dự đoán.
              </EmptyState>
            )}

            {loadingDetail && <LoadingSkeleton count={2} variant="row" />}
            {detailError && <Alert tone="danger">{detailError}</Alert>}

            {detail && (
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h3 className="text-base font-bold text-slate-900 m-0">
                      {detail.maYeuCau || detail.requestCode}
                    </h3>
                    {detail.resultMessage && (
                      <p className="text-xs text-slate-500 mt-1 m-0 leading-relaxed">
                        {detail.resultMessage}
                      </p>
                    )}
                  </div>
                  <Badge tone="cyan">
                    {detail.nguonDiem || detail.scoreSource || "UNKNOWN"}
                  </Badge>
                </div>

                {/* Meta grid */}
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">Loại dự đoán</span>
                    <strong className="block text-slate-800 mt-0.5">
                      {TYPE_LABEL[detail.kieuDuDoan || detail.predictionType] ||
                        detail.kieuDuDoan ||
                        detail.predictionType}
                    </strong>
                  </div>
                  <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                    <span className="text-slate-400">Số kết quả</span>
                    <strong className="block text-slate-800 mt-0.5">
                      {detail.results?.length ?? 0}
                    </strong>
                  </div>
                  {(detail.nguongDiem ?? detail.scoreThreshold) != null && (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="text-slate-400">Ngưỡng điểm</span>
                      <strong className="block text-slate-800 mt-0.5">
                        {detail.nguongDiem ?? detail.scoreThreshold}
                      </strong>
                    </div>
                  )}
                  {(detail.soKetQuaToiDa ?? detail.topK) != null && (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100">
                      <span className="text-slate-400">Top K</span>
                      <strong className="block text-slate-800 mt-0.5">
                        {detail.soKetQuaToiDa ?? detail.topK}
                      </strong>
                    </div>
                  )}
                  {(detail.tenThuoc || detail.drugName) && (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 col-span-2">
                      <span className="text-slate-400">Thuốc đầu vào</span>
                      <strong className="block text-slate-800 mt-0.5">
                        {detail.tenThuoc || detail.drugName}
                      </strong>
                    </div>
                  )}
                  {(detail.tenBenh || detail.diseaseName) && (
                    <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-100 col-span-2">
                      <span className="text-slate-400">Bệnh/chỉ định đầu vào</span>
                      <strong className="block text-slate-800 mt-0.5">
                        {detail.tenBenh || detail.diseaseName}
                      </strong>
                    </div>
                  )}
                </div>

                {/* Results */}
                <div className="space-y-2.5">
                  {(detail.results ?? []).map((result, i) => (
                    <PredictionResultCard
                      key={
                        result.ketQuaDuDoanId || result.predictionResultId
                      }
                      result={result}
                      index={i}
                    />
                  ))}
                </div>
              </div>
            )}
          </Card>
        </div>
      )}
    </section>
  );
}
