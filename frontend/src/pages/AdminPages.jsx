import { Database, Settings } from "lucide-react";
import { api } from "../api";
import { DiseaseCard, MedicineCard } from "../components/medical";
import { Alert, Badge, Card, EmptyState, LoadingSkeleton } from "../components/ui";
import { useLoad } from "../hooks/useLoad";
import { getItems, getTotal } from "../utils/format";

export function AdminDashboardPage() {
  return (
    <section className="space-y-5">
      <Card className="!p-4">
        <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
          Admin hidden
        </span>
        <h2 className="text-lg font-bold text-slate-900 m-0">
          Trang quản trị cũ đã được ẩn
        </h2>
        <p className="text-sm text-slate-500 mt-1 m-0">
          Khu vực điều hướng chính hiện dùng dashboard chung, tra cứu, dự đoán AI, lịch sử và phản hồi theo role.
        </p>
      </Card>
    </section>
  );
}

export function AdminCatalogPage() {
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 6 }), []);
  const diseases = useLoad(() => api.getDiseases({ page: 1, pageSize: 6 }), []);

  return (
    <section className="space-y-5">
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
