import {
  Activity,
  ArrowRight,
  Beaker,
  Brain,
  CheckCircle2,
  Database,
  History,
  Pill,
  Sparkles,
  Stethoscope,
  Target,
} from "lucide-react";
import { useMemo } from "react";
import { api } from "../api";
import { MedicalWarning, StatCard } from "../components/medical";
import { Alert, Button, Card, EmptyState, LoadingSkeleton } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { formatDateTime, getItems, getTotal } from "../utils/format";

const WORKFLOW_STEPS = [
  {
    icon: Database,
    title: "Chuẩn hóa dữ liệu",
    desc: "Import và chuẩn hóa dữ liệu thuốc, bệnh/chỉ định từ DataThuoc.",
  },
  {
    icon: Target,
    title: "Chọn hướng phân tích",
    desc: "Chọn thuốc → bệnh hoặc bệnh → thuốc để khởi tạo dự đoán.",
  },
  {
    icon: Brain,
    title: "AI / Fallback chấm điểm",
    desc: "Mô hình AI hoặc dữ liệu liên kết sẵn có tính điểm tin cậy.",
  },
  {
    icon: Sparkles,
    title: "Xếp hạng kết quả",
    desc: "Kết quả được xếp hạng theo điểm, mức tin cậy và loại liên kết.",
  },
  {
    icon: CheckCircle2,
    title: "Lưu lịch sử",
    desc: "Toàn bộ kết quả được lưu để đối chiếu, đánh giá và phản hồi.",
  },
];

const QUICK_ACTIONS = [
  { id: "catalog", icon: Pill, label: "Tra cứu thuốc/bệnh", desc: "Tìm thuốc, bệnh/chỉ định và xem chi tiết" },
  { id: "prediction", icon: Beaker, label: "Tạo dự đoán AI", desc: "Phân tích liên kết thuốc-bệnh" },
  { id: "history", icon: History, label: "Xem lịch sử", desc: "Theo dõi các dự đoán đã thực hiện" },
];

const TYPE_LABELS = {
  DRUG_TO_DISEASE: "Thuốc → Bệnh",
  DISEASE_TO_DRUG: "Bệnh → Thuốc",
  PAIR_CHECK: "Kiểm tra cặp",
  PAIR_PREDICTION: "Kiểm tra cặp",
};

const TYPE_COLORS = ["#14b8a6", "#06b6d4", "#22c55e", "#f59e0b"];

function toDateBucket(value) {
  if (!value) {
    return { key: "unknown", label: "Chưa rõ ngày" };
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return { key: "unknown", label: "Chưa rõ ngày" };
  }

  return {
    key: date.toISOString().slice(0, 10),
    label: new Intl.DateTimeFormat("vi-VN", {
      day: "2-digit",
      month: "2-digit",
    }).format(date),
  };
}

function buildAnalytics(items) {
  const byDate = new Map();
  const byType = new Map();
  const bySource = new Map();

  items.forEach((item) => {
    const dateBucket = toDateBucket(item.ngayTao || item.createdAt);
    const currentDate = byDate.get(dateBucket.key) || {
      key: dateBucket.key,
      date: dateBucket.label,
      count: 0,
    };
    currentDate.count += 1;
    byDate.set(dateBucket.key, currentDate);

    const type = item.kieuDuDoan || item.predictionType || "UNKNOWN";
    byType.set(type, (byType.get(type) || 0) + 1);

    const source = item.nguonDiem || item.scoreSource;
    if (source) bySource.set(source, (bySource.get(source) || 0) + 1);
  });

  return {
    byDate: Array.from(byDate.values())
      .sort((a, b) => a.key.localeCompare(b.key))
      .slice(-10),
    byType: Array.from(byType, ([type, count]) => ({
      type,
      label: TYPE_LABELS[type] || type,
      count,
    })).sort((a, b) => b.count - a.count),
    bySource: Array.from(bySource, ([source, count]) => ({ source, count })),
  };
}

function ActivityBarChart({ data }) {
  const maxCount = Math.max(1, ...data.map((item) => item.count));

  return (
    <div className="h-64 min-w-0 rounded-xl border border-slate-100 bg-white px-3 py-4">
      <div
        className="grid h-full items-end gap-3"
        style={{ gridTemplateColumns: `repeat(${data.length}, minmax(34px, 1fr))` }}
      >
        {data.map((item) => {
          const height = Math.max(10, Math.round((item.count / maxCount) * 100));

          return (
            <div
              key={item.key}
              className="flex h-full min-w-0 flex-col items-center justify-end gap-2"
              title={`${item.date}: ${item.count} yêu cầu dự đoán`}
            >
              <span className="text-xs font-bold text-slate-700">{item.count}</span>
              <div className="flex min-h-0 w-full flex-1 items-end justify-center border-b border-slate-200">
                <span
                  className="block w-full max-w-12 rounded-t-lg bg-gradient-to-t from-teal-500 to-cyan-400 shadow-[0_8px_20px_rgba(20,184,166,0.20)]"
                  style={{ height: `${height}%` }}
                  aria-label={`${item.count} yêu cầu ngày ${item.date}`}
                />
              </div>
              <span className="truncate text-[11px] font-semibold text-slate-400">{item.date}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function buildDonutGradient(items) {
  const total = items.reduce((sum, item) => sum + item.count, 0);
  if (!total) return "#e2e8f0";

  let cursor = 0;
  const segments = items.map((item, index) => {
    const start = cursor;
    const end = cursor + (item.count / total) * 100;
    cursor = end;
    const color = TYPE_COLORS[index % TYPE_COLORS.length];
    return `${color} ${start}% ${end}%`;
  });

  return `conic-gradient(${segments.join(", ")})`;
}

function PredictionTypeDonut({ data }) {
  const total = data.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="mt-3 flex justify-center">
      <div
        className="relative h-48 w-48 rounded-full shadow-[inset_0_0_0_1px_rgba(148,163,184,0.16)]"
        style={{ background: buildDonutGradient(data) }}
        role="img"
        aria-label={`Phân bố ${total} yêu cầu dự đoán theo loại`}
      >
        <div className="absolute inset-10 grid place-items-center rounded-full bg-white text-center shadow-inner">
          <span>
            <strong className="block text-2xl font-black text-slate-900">{total}</strong>
            <small className="text-xs font-semibold text-slate-400">yêu cầu</small>
          </span>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage({ onNavigate, health }) {
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 1 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 1 }), []);
  const history = useLoad(() => api.getPredictionHistory(), []);

  const loading = drugs.loading || diseases.loading || history.loading;
  const historyItems = getItems(history.data);
  const recent = historyItems.slice(0, 5);
  const analytics = useMemo(() => buildAnalytics(historyItems), [historyItems]);
  const hasAnalytics = historyItems.length > 0;

  return (
    <section className="space-y-6">
      {/* ── Hero Panel ── */}
      <Card className="!p-0 overflow-hidden">
        <div className="p-6 sm:p-8">
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-2">
              Medical AI Clinical Dashboard
            </span>
            <h2 className="text-3xl sm:text-4xl font-black text-slate-900 m-0 leading-tight">
              DrugDiseaseML
            </h2>
            <p className="text-slate-600 mt-3 mb-0 text-sm sm:text-base leading-relaxed max-w-3xl">
              Nền tảng hỗ trợ phân tích liên kết thuốc-bệnh bằng AI, kết hợp dữ liệu
              dược học và cảnh báo an toàn y tế.
            </p>
            <p className="text-slate-500 mt-2 mb-0 text-xs sm:text-sm leading-relaxed max-w-3xl">
              Tra cứu dữ liệu thuốc, bệnh/chỉ định và phân tích liên kết bằng mô hình
              AI kết hợp dữ liệu lâm sàng có kiểm soát.
            </p>
            <div className="flex flex-wrap gap-3 mt-6">
              <Button onClick={() => onNavigate("prediction")}>
                <Beaker size={18} />
                Tạo dự đoán mới
              </Button>
              <Button variant="secondary" onClick={() => onNavigate("catalog")}>
                <Pill size={18} />
                Tra cứu thuốc/bệnh
              </Button>
            </div>
        </div>
      </Card>

      {/* ── Stat Cards ── */}
      {loading ? (
        <LoadingSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <StatCard
            icon={Pill}
            label="Tổng số thuốc"
            value={getTotal(drugs.data)}
            hint="Từ bảng Thuoc"
            tone="teal"
          />
          <StatCard
            icon={Stethoscope}
            label="Bệnh / chỉ định"
            value={getTotal(diseases.data)}
            hint="Từ bảng Benh"
            tone="cyan"
          />
          <StatCard
            icon={Activity}
            label="Yêu cầu dự đoán"
            value={getItems(history.data).length}
            hint="Lịch sử người dùng"
            tone="blue"
          />
        </div>
      )}

      {/* ── Analytics Panel ── */}
      <Card>
        <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between mb-4">
          <div>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              Clinical analytics
            </span>
            <h3 className="text-lg font-bold text-slate-900 m-0">
              Tín hiệu hoạt động dự đoán
            </h3>
            <p className="text-sm text-slate-500 mt-1 m-0 max-w-2xl">
              Biểu đồ được tổng hợp từ lịch sử dự đoán thật của người dùng hiện tại.
            </p>
          </div>
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wide">
            {historyItems.length} yêu cầu
          </span>
        </div>

        {history.loading ? (
          <LoadingSkeleton count={2} variant="row" />
        ) : !hasAnalytics ? (
          <EmptyState icon={Activity} title="Chưa có đủ dữ liệu để hiển thị biểu đồ">
            Hãy tạo thêm dự đoán để hệ thống tổng hợp thống kê.
          </EmptyState>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-[1.35fr,0.65fr] gap-4">
            <div className="rounded-2xl border border-slate-100 bg-slate-50/50 p-4 min-w-0">
              <div className="flex items-center justify-between gap-3 mb-3">
                <strong className="text-sm text-slate-800">Lịch sử dự đoán theo ngày</strong>
                <span className="text-xs text-slate-400">10 ngày gần nhất có dữ liệu</span>
              </div>
              <ActivityBarChart data={analytics.byDate} />
            </div>

            <div className="rounded-2xl border border-slate-100 bg-slate-50/50 p-4 min-w-0">
              <strong className="text-sm text-slate-800">Phân bố loại dự đoán</strong>
              {analytics.byType.length === 0 ? (
                <p className="text-sm text-slate-500 mt-3 m-0">
                  Chưa có dữ liệu loại dự đoán.
                </p>
              ) : (
                <>
                  <PredictionTypeDonut data={analytics.byType} />
                  <div className="grid gap-2">
                    {analytics.byType.map((item, index) => (
                      <div key={item.type} className="flex items-center justify-between gap-2 text-xs">
                        <span className="flex items-center gap-2 text-slate-600">
                          <span
                            className="h-2.5 w-2.5 rounded-full"
                            style={{ backgroundColor: TYPE_COLORS[index % TYPE_COLORS.length] }}
                          />
                          {item.label}
                        </span>
                        <strong className="text-slate-800">{item.count}</strong>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>
        )}

        {analytics.bySource.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {analytics.bySource.map((item) => (
              <span
                key={item.source}
                className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-bold text-slate-600"
              >
                {item.source}: {item.count}
              </span>
            ))}
          </div>
        )}
      </Card>

      {/* ── Workflow Panel ── */}
      <Card>
        <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
          Quy trình phân tích
        </span>
        <h3 className="text-lg font-bold text-slate-900 m-0 mb-4">
          Workflow dự đoán liên kết thuốc-bệnh
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          {WORKFLOW_STEPS.map((step, i) => {
            const StepIcon = step.icon;
            return (
              <div
                key={i}
                className="relative flex flex-col items-center text-center p-4 rounded-[var(--radius-md)] bg-slate-50/80 border border-slate-100"
              >
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-teal-100 to-cyan-100 flex items-center justify-center text-teal-600 mb-2">
                  <StepIcon size={20} />
                </div>
                <span className="text-xs font-bold text-teal-700 mb-0.5">
                  Bước {i + 1}
                </span>
                <strong className="text-sm text-slate-800 leading-snug">
                  {step.title}
                </strong>
                <p className="text-xs text-slate-500 mt-1 m-0 leading-relaxed">
                  {step.desc}
                </p>
                {/* Connector arrow - hidden on mobile, hidden for last item */}
                {i < WORKFLOW_STEPS.length - 1 && (
                  <ArrowRight
                    size={16}
                    className="hidden lg:block absolute -right-3.5 top-1/2 -translate-y-1/2 text-slate-300 z-10"
                  />
                )}
              </div>
            );
          })}
        </div>
      </Card>

      {/* ── Bottom Grid: Medical Warning + Recent + Quick Actions ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* System Status + Medical Warning */}
        <div className="space-y-4">
          <Card>
            <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
              System intelligence
            </span>
            <h3 className="text-base font-bold text-slate-900 m-0 mb-3">
              Trạng thái hệ thống
            </h3>
            <div className="space-y-2.5">
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <Database size={16} className="text-slate-400" />
                  <span className="text-sm text-slate-600">Backend</span>
                </div>
                <strong className="text-sm text-slate-800">
                  {health?.status === "healthy" ? "Online" : "Chưa rõ"}
                </strong>
              </div>
              <div className="flex items-center justify-between py-2">
                <div className="flex items-center gap-2.5">
                  <Brain size={16} className="text-slate-400" />
                  <span className="text-sm text-slate-600">AI service</span>
                </div>
                <strong className="text-sm text-slate-800">
                  {health?.aiStatus === "healthy" ? "Ready" : "Fallback"}
                </strong>
              </div>
            </div>
            {health?.aiStatus !== "healthy" && (
              <Alert tone="warning" className="mt-3">
                AI service chưa khả dụng. Hệ thống có thể dùng điểm liên kết trong
                database để thay thế.
              </Alert>
            )}
          </Card>

          <MedicalWarning />
        </div>

        {/* Recent Activity */}
        <Card>
          <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
            Recent activity
          </span>
          <h3 className="text-base font-bold text-slate-900 m-0 mb-3">
            Dự đoán gần đây
          </h3>
          {history.error && <Alert tone="danger">{history.error}</Alert>}
          {!history.loading && recent.length === 0 && (
            <EmptyState title="Chưa có yêu cầu dự đoán">
              Tạo dự đoán mới để theo dõi tại đây.
            </EmptyState>
          )}
          <div className="space-y-2">
            {recent.map((item) => (
              <button
                key={item.yeuCauDuDoanId || item.requestId}
                onClick={() => onNavigate("history")}
                className="w-full flex flex-col gap-1 p-3 rounded-[var(--radius-md)] border border-slate-100 bg-slate-50/50 hover:bg-slate-100/80 transition-colors text-left cursor-pointer"
                style={{ border: '1px solid #eef2f7' }}
              >
                <span className="text-xs font-semibold text-teal-600">
                  {item.maYeuCau || item.requestCode}
                </span>
                <strong className="text-sm text-slate-800">
                  {item.kieuDuDoan || item.predictionType}
                </strong>
                <small className="text-xs text-slate-400">
                  {formatDateTime(item.ngayTao || item.createdAt)}
                </small>
              </button>
            ))}
          </div>
        </Card>

        {/* Quick Actions */}
        <Card>
          <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
            Quick actions
          </span>
          <h3 className="text-base font-bold text-slate-900 m-0 mb-3">
            Truy cập nhanh
          </h3>
          <div className="space-y-2">
            {QUICK_ACTIONS.map((action) => {
              const ActionIcon = action.icon;
              return (
                <button
                  key={action.id}
                  onClick={() => onNavigate(action.id)}
                  className="w-full flex items-center gap-3 p-3 rounded-[var(--radius-md)] border border-slate-100 bg-white hover:bg-teal-50/50 hover:border-teal-200/50 transition-all duration-200 text-left cursor-pointer group"
                >
                  <div className="w-9 h-9 rounded-xl bg-slate-100 group-hover:bg-teal-100 flex items-center justify-center text-slate-500 group-hover:text-teal-600 transition-colors shrink-0">
                    <ActionIcon size={18} />
                  </div>
                  <div className="min-w-0">
                    <strong className="block text-sm text-slate-800">{action.label}</strong>
                    <span className="text-xs text-slate-500">{action.desc}</span>
                  </div>
                  <ArrowRight
                    size={16}
                    className="ml-auto text-slate-300 group-hover:text-teal-500 transition-colors shrink-0"
                  />
                </button>
              );
            })}
          </div>
        </Card>
      </div>
    </section>
  );
}
