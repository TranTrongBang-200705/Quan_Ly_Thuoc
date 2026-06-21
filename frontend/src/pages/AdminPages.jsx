import { Database, Link2, Pill, Settings, Stethoscope, Users } from "lucide-react";
import { api } from "../api";
import { DiseaseCard, MedicineCard, StatCard } from "../components/medical";
import { Alert, Badge, Card, EmptyState, LoadingSkeleton, PageHeader } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { getItems, getTotal } from "../utils/format";

export function AdminDashboardPage() {
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 1 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 1 }), []);
  const links = useLoad(() => api.getAdminLinks({}), []);
  const predictions = useLoad(() => api.getAdminPredictionHistory({}), []);

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Admin control"
        title="Tổng quan quản trị"
        subtitle="Giám sát dữ liệu thuốc-bệnh, liên kết và các yêu cầu dự đoán."
      />

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Pill} label="Thuốc" value={getTotal(drugs.data)} hint="Catalog DataThuoc" />
        <StatCard icon={Stethoscope} label="Bệnh" value={getTotal(diseases.data)} hint="Clinical indications" tone="cyan" />
        <StatCard icon={Link2} label="Liên kết" value={getItems(links.data).length} hint="Đang hiển thị" tone="emerald" />
        <StatCard icon={Users} label="Dự đoán" value={getItems(predictions.data).length} hint="Admin history" tone="blue" />
      </div>

      {(drugs.error || diseases.error || links.error || predictions.error) && (
        <Alert tone="danger">{drugs.error || diseases.error || links.error || predictions.error}</Alert>
      )}

      <Card>
        <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">Operational note</span>
        <h3 className="text-base font-bold text-slate-900 m-0">Quản trị dữ liệu</h3>
        <p className="text-sm text-slate-500 mt-1 m-0">Giao diện đang dùng các endpoint backend hiện có. Các thao tác thêm/sửa/xóa chỉ hiển thị khi backend cung cấp endpoint tương ứng.</p>
      </Card>
    </section>
  );
}

export function AdminCatalogPage() {
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 6 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 6 }), []);

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="Catalog monitor"
        title="Dữ liệu thuốc và bệnh"
        subtitle="Xem nhanh mẫu dữ liệu để kiểm tra chất lượng catalog y dược."
      />

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 items-start">
        <Card className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 m-0">Thuốc mới trong catalog</h3>
            <Badge tone="cyan">{getTotal(drugs.data)} thuốc</Badge>
          </div>
          {drugs.error && <Alert tone="danger">{drugs.error}</Alert>}
          {drugs.loading ? <LoadingSkeleton count={3} /> : (
            <div className="space-y-3">
              {getItems(drugs.data).map((drug) => <MedicineCard key={drug.thuocId || drug.drugId} drug={drug} />)}
            </div>
          )}
        </Card>

        <Card className="space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="text-base font-bold text-slate-900 m-0">Bệnh / chỉ định</h3>
            <Badge tone="blue">{getTotal(diseases.data)} bệnh</Badge>
          </div>
          {diseases.error && <Alert tone="danger">{diseases.error}</Alert>}
          {diseases.loading ? <LoadingSkeleton count={3} /> : (
            <div className="space-y-3">
              {getItems(diseases.data).map((disease) => <DiseaseCard key={disease.benhId || disease.diseaseId} disease={disease} />)}
            </div>
          )}
        </Card>
      </div>
    </section>
  );
}

export function AdminLookupsPage() {
  const lookups = useLoad(() => api.getLookups(), []);
  const groups = [
    ["Loại dự đoán", lookups.data?.predictionTypes ?? []],
    ["Mức tin cậy", lookups.data?.confidenceLevels ?? []],
    ["Loại liên kết", lookups.data?.linkTypes ?? []],
    ["Trạng thái kiểm duyệt", lookups.data?.evidenceStatuses ?? []],
    ["Nhóm thuốc", lookups.data?.nhomThuoc ?? []],
    ["Nhóm bệnh", lookups.data?.nhomBenh ?? []],
  ];

  return (
    <section className="space-y-5">
      <PageHeader
        eyebrow="System taxonomy"
        title="Danh mục hệ thống"
        subtitle="Các lookup đang được backend trả về cho UI và form nghiệp vụ."
      />
      {lookups.error && <Alert tone="danger">{lookups.error}</Alert>}
      {lookups.loading ? (
        <LoadingSkeleton count={6} />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {groups.map(([title, items]) => (
            <Card key={title} className="!p-0 overflow-hidden">
              <div className="flex items-center gap-2 p-3 bg-slate-50 border-b border-slate-100">
                <Settings size={16} className="text-slate-400" />
                <h3 className="text-sm font-bold text-slate-800 m-0">{title}</h3>
              </div>
              <div className="p-3">
                {items.length === 0 ? (
                  <EmptyState icon={Database} title="Chưa có dữ liệu" />
                ) : (
                  <ul className="space-y-2 m-0 p-0 list-none text-xs">
                    {items.slice(0, 12).map((item) => (
                      <li key={`${title}-${item.id || item.code}`} className="flex items-center gap-2">
                        <code className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-mono">
                          {item.code}
                        </code>
                        <span className="text-slate-700">{item.name}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </section>
  );
}
