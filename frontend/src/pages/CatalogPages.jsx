import { Link2, Pill, Search, Stethoscope } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import { api } from "../api";
import {
  DiseaseCard,
  DiseaseDetailModal,
  DrugDetailModal,
  MedicineCard,
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
import { useLoad } from "../hooks/useLoad";
import { formatScore, getItems, getTotal, pageCount, truncate } from "../utils/format";
import { filterAndRankCatalog } from "../utils/search";

const CATALOG_PAGE_SIZE = 20000;
const GROUP_LIMIT_STEP = 12;

function useDebouncedValue(value, delay = 250) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}

function drugSearchFields(drug) {
  return [
    { value: drug.tenThuoc || drug.drugName || drug.activeName, weight: 1.45 },
    { value: drug.tenThuocGoc || drug.tradeName, weight: 1.2 },
    { value: drug.hoatChat, weight: 1.3 },
    { value: drug.congDung || drug.knownIndications, weight: 1 },
    { value: drug.tenNhomThuoc, weight: 0.9 },
    { value: drug.dangBaoChe, weight: 0.55 },
  ];
}

function diseaseSearchFields(disease) {
  return [
    { value: disease.tenBenh || disease.diseaseName, weight: 1.45 },
    { value: disease.tenDongNghia, weight: 1.25 },
    { value: disease.moTa || disease.description, weight: 1 },
    { value: disease.trieuChung, weight: 1 },
    { value: disease.thuocDieuTriDaBiet, weight: 0.75 },
    { value: disease.tenNhomBenh, weight: 0.95 },
  ];
}

function ResultGroup({
  title,
  icon: Icon,
  items,
  visibleCount,
  onShowMore,
  children,
}) {
  if (!items.length) return null;
  const visibleItems = items.slice(0, visibleCount);
  const remaining = items.length - visibleItems.length;

  return (
    <section className="space-y-3">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="flex items-center gap-2 text-lg font-extrabold text-slate-900 m-0">
            <Icon size={20} className="text-teal-600" />
            {title}
          </h2>
          <p className="text-sm text-slate-500 mt-0.5 m-0">
            {items.length} kết quả phù hợp
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {visibleItems.map(children)}
      </div>

      {remaining > 0 && (
        <div className="flex justify-center pt-1">
          <Button type="button" variant="secondary" onClick={onShowMore}>
            Xem thêm {Math.min(GROUP_LIMIT_STEP, remaining)} kết quả
          </Button>
        </div>
      )}
    </section>
  );
}

export function CatalogPage() {
  const [keyword, setKeyword] = useState("");
  const [drugVisibleCount, setDrugVisibleCount] = useState(GROUP_LIMIT_STEP);
  const [diseaseVisibleCount, setDiseaseVisibleCount] = useState(GROUP_LIMIT_STEP);
  const [detailDrug, setDetailDrug] = useState(null);
  const [detailDisease, setDetailDisease] = useState(null);
  const debouncedKeyword = useDebouncedValue(keyword, 250);
  const query = debouncedKeyword.trim();

  useEffect(() => {
    setDrugVisibleCount(GROUP_LIMIT_STEP);
    setDiseaseVisibleCount(GROUP_LIMIT_STEP);
  }, [query]);

  const drugs = useLoad(
    () => api.getDrugs({ page: 1, pageSize: CATALOG_PAGE_SIZE }),
    [],
  );
  const diseases = useLoad(
    () => api.getDiseases({ page: 1, pageSize: CATALOG_PAGE_SIZE }),
    [],
  );

  const drugItems = getItems(drugs.data);
  const diseaseItems = getItems(diseases.data);
  const drugResults = useMemo(
    () => filterAndRankCatalog(drugItems, query, drugSearchFields),
    [drugItems, query],
  );
  const diseaseResults = useMemo(
    () => filterAndRankCatalog(diseaseItems, query, diseaseSearchFields),
    [diseaseItems, query],
  );
  const loading = drugs.loading || diseases.loading;
  const error = drugs.error || diseases.error;
  const totalMatches = drugResults.total + diseaseResults.total;
  const aliasUsed = drugResults.aliasUsed || diseaseResults.aliasUsed;

  return (
    <section className="space-y-5">
      <Card className="!p-4">
        <form className="flex flex-col gap-3" onSubmit={(event) => event.preventDefault()}>
          <Input
            icon={Search}
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            placeholder="Nhập tên thuốc, hoạt chất, bệnh, triệu chứng hoặc chỉ định..."
          />
          <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
            <p className="text-sm text-slate-500 m-0">
              {query
                ? (
                  <>
                    Hiển thị <strong className="text-slate-700">{totalMatches}</strong> kết quả phù hợp cho &ldquo;{query}&rdquo;
                  </>
                )
                : (
                  <>
                    Nhập từ khóa để tìm trong <strong className="text-slate-700">{drugItems.length}</strong> thuốc và{" "}
                    <strong className="text-slate-700">{diseaseItems.length}</strong> bệnh/chỉ định.
                  </>
                )}
            </p>
            {aliasUsed && query && (
              <span className="text-xs font-semibold text-teal-600">
                Đã mở rộng tìm kiếm theo thuật ngữ liên quan
              </span>
            )}
          </div>
        </form>
      </Card>

      {error && (
        <Alert tone="danger">
          Không thể tải dữ liệu catalog. Vui lòng kiểm tra kết nối Backend hoặc thử lại.
        </Alert>
      )}

      {loading ? (
        <LoadingSkeleton count={6} />
      ) : !query ? (
        <EmptyState icon={Search} title="Sẵn sàng tra cứu thuốc/bệnh">
          Nhập tên thuốc, hoạt chất, bệnh, triệu chứng hoặc chỉ định để tìm kiếm
          trong toàn bộ catalog.
        </EmptyState>
      ) : totalMatches === 0 ? (
        <EmptyState icon={Search} title="Không tìm thấy kết quả phù hợp">
          Thử đổi từ khóa, nhập không dấu hoặc dùng thuật ngữ y khoa liên quan.
        </EmptyState>
      ) : (
        <div className="space-y-7">
          <ResultGroup
            title="Thuốc phù hợp"
            icon={Pill}
            items={drugResults.items}
            visibleCount={drugVisibleCount}
            onShowMore={() => setDrugVisibleCount((current) => current + GROUP_LIMIT_STEP)}
          >
            {(drug) => (
              <MedicineCard
                key={drug.thuocId || drug.drugId}
                drug={drug}
                onDetail={setDetailDrug}
              />
            )}
          </ResultGroup>

          <ResultGroup
            title="Bệnh/chỉ định phù hợp"
            icon={Stethoscope}
            items={diseaseResults.items}
            visibleCount={diseaseVisibleCount}
            onShowMore={() => setDiseaseVisibleCount((current) => current + GROUP_LIMIT_STEP)}
          >
            {(disease) => (
              <DiseaseCard
                key={disease.benhId || disease.diseaseId}
                disease={disease}
                onDetail={setDetailDisease}
              />
            )}
          </ResultGroup>
        </div>
      )}

      <DrugDetailModal drug={detailDrug} onClose={() => setDetailDrug(null)} />
      <DiseaseDetailModal disease={detailDisease} onClose={() => setDetailDisease(null)} />
    </section>
  );
}

/* ── Pagination ── */
function Pagination({ page, total, pageSize, onPage }) {
  const pages = pageCount(total, pageSize);
  if (pages <= 1) return null;
  return (
    <div className="flex items-center gap-2">
      <Button
        variant="secondary"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
      >
        Trước
      </Button>
      <span className="text-xs font-semibold text-slate-500 px-2">
        Trang {page} / {pages}
      </span>
      <Button
        variant="secondary"
        size="sm"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
      >
        Sau
      </Button>
    </div>
  );
}

/* ══════════════════════════════════════════════
   DRUGS PAGE
   ══════════════════════════════════════════════ */
export function DrugsPage({ embedded = false }) {
  const [keyword, setKeyword] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [detailDrug, setDetailDrug] = useState(null);
  const pageSize = 12;

  const state = useLoad(
    () => api.getDrugs({ tuKhoa: query, page, pageSize }),
    [query, page]
  );
  const items = getItems(state.data);
  const total = getTotal(state.data);

  function search(event) {
    event.preventDefault();
    setPage(1);
    setQuery(keyword.trim());
  }

  return (
    <section className="space-y-5">
      {/* Search bar */}
      <Card className="!p-4">
        <form className="flex flex-col sm:flex-row gap-3" onSubmit={search}>
          <div className="flex-1">
            <Input
              icon={Search}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Tìm thuốc, hoạt chất, nhà sản xuất..."
            />
          </div>
          <Button className="shrink-0">
            <Search size={16} />
            Tìm kiếm
          </Button>
        </form>
      </Card>

      {/* Error */}
      {state.error && (
        <Alert tone="danger">
          Không thể tải danh sách thuốc. Vui lòng kiểm tra kết nối Backend hoặc thử lại.
        </Alert>
      )}

      {/* Loading */}
      {state.loading ? (
        <LoadingSkeleton count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={Pill} title="Không tìm thấy thuốc">
          {query
            ? `Không có kết quả phù hợp với "${query}". Thử đổi từ khóa hoặc xóa bộ lọc.`
            : "Chưa có dữ liệu thuốc trong hệ thống."}
        </EmptyState>
      ) : (
        <>
          {/* Toolbar */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <span className="text-sm text-slate-500">
              Hiển thị{" "}
              <strong className="text-slate-700">{items.length}</strong> /{" "}
              <strong className="text-slate-700">{total}</strong> thuốc
              {query && (
                <span className="ml-1 text-teal-600">
                  cho &ldquo;{query}&rdquo;
                </span>
              )}
            </span>
            <Pagination
              page={page}
              total={total}
              pageSize={pageSize}
              onPage={setPage}
            />
          </div>

          {/* Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((drug) => (
              <MedicineCard
                key={drug.thuocId || drug.drugId}
                drug={drug}
                onDetail={setDetailDrug}
              />
            ))}
          </div>

          {/* Bottom pagination */}
          {total > pageSize && (
            <div className="flex justify-center pt-2">
              <Pagination
                page={page}
                total={total}
                pageSize={pageSize}
                onPage={setPage}
              />
            </div>
          )}
        </>
      )}

      {/* Detail modal */}
      <DrugDetailModal drug={detailDrug} onClose={() => setDetailDrug(null)} />
    </section>
  );
}

/* ══════════════════════════════════════════════
   DISEASES PAGE
   ══════════════════════════════════════════════ */
export function DiseasesPage({ embedded = false }) {
  const [keyword, setKeyword] = useState("");
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [detailDisease, setDetailDisease] = useState(null);
  const pageSize = 12;

  const state = useLoad(
    () => api.getDiseases({ tuKhoa: query, page, pageSize }),
    [query, page]
  );
  const items = getItems(state.data);
  const total = getTotal(state.data);

  function search(event) {
    event.preventDefault();
    setPage(1);
    setQuery(keyword.trim());
  }

  return (
    <section className="space-y-5">
      {/* Search */}
      <Card className="!p-4">
        <form className="flex flex-col sm:flex-row gap-3" onSubmit={search}>
          <div className="flex-1">
            <Input
              icon={Search}
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="Tìm bệnh, chỉ định, triệu chứng..."
            />
          </div>
          <Button className="shrink-0">
            <Search size={16} />
            Tìm kiếm
          </Button>
        </form>
      </Card>

      {state.error && (
        <Alert tone="danger">
          Không thể tải danh sách bệnh/chỉ định. Vui lòng kiểm tra kết nối Backend hoặc thử lại.
        </Alert>
      )}

      {state.loading ? (
        <LoadingSkeleton count={6} />
      ) : items.length === 0 ? (
        <EmptyState icon={Stethoscope} title="Không tìm thấy bệnh/chỉ định">
          {query
            ? `Không có kết quả phù hợp với "${query}". Thử nhập tên bệnh, triệu chứng hoặc mô tả khác.`
            : "Chưa có dữ liệu bệnh/chỉ định trong hệ thống."}
        </EmptyState>
      ) : (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <span className="text-sm text-slate-500">
              Hiển thị{" "}
              <strong className="text-slate-700">{items.length}</strong> /{" "}
              <strong className="text-slate-700">{total}</strong> bệnh/chỉ định
              {query && (
                <span className="ml-1 text-teal-600">
                  cho &ldquo;{query}&rdquo;
                </span>
              )}
            </span>
            <Pagination
              page={page}
              total={total}
              pageSize={pageSize}
              onPage={setPage}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {items.map((disease) => (
              <DiseaseCard
                key={disease.benhId || disease.diseaseId}
                disease={disease}
                onDetail={setDetailDisease}
              />
            ))}
          </div>

          {total > pageSize && (
            <div className="flex justify-center pt-2">
              <Pagination
                page={page}
                total={total}
                pageSize={pageSize}
                onPage={setPage}
              />
            </div>
          )}
        </>
      )}

      {/* Detail modal */}
      <DiseaseDetailModal
        disease={detailDisease}
        onClose={() => setDetailDisease(null)}
      />
    </section>
  );
}

/* ── Confidence levels for filter ── */
const CONFIDENCE_LEVELS = ["Cao", "Trung bình", "Thấp"];

/* ══════════════════════════════════════════════
   LINKS PAGE
   ══════════════════════════════════════════════ */
export function LinksPage({ admin = false }) {
  if (!admin) {
    return (
      <Alert tone="danger">
        Bạn không có quyền truy cập dữ liệu liên kết thuốc-bệnh nội bộ.
      </Alert>
    );
  }

  return <AdminLinksPage />;
}

function AdminLinksPage() {
  /* Filter state */
  const [drugKeyword, setDrugKeyword] = useState("");
  const [diseaseKeyword, setDiseaseKeyword] = useState("");
  const [confidenceFilter, setConfidenceFilter] = useState("");
  const [params, setParams] = useState({});

  const state = useLoad(
    () => api.getAdminLinks(params),
    [JSON.stringify(params)]
  );

  /* Load drug/disease lists for select filters */
  const drugs = useLoad(() => api.getDrugs({ page: 1, pageSize: 200 }), []);
  const diseases = useLoad(
    () => api.getDiseases({ page: 1, pageSize: 200 }),
    []
  );
  const drugOptions = getItems(drugs.data);
  const diseaseOptions = getItems(diseases.data);

  const allItems = getItems(state.data);

  /* Client-side filter by name keyword + confidence */
  const items = allItems.filter((link) => {
    const tName = (link.tenThuoc || link.drugName || "").toLowerCase();
    const dName = (link.tenBenh || link.diseaseName || "").toLowerCase();
    const conf = (
      link.tenMucTinCay ||
      link.confidenceLevel ||
      ""
    ).toLowerCase();

    const matchDrug = drugKeyword
      ? tName.includes(drugKeyword.toLowerCase())
      : true;
    const matchDisease = diseaseKeyword
      ? dName.includes(diseaseKeyword.toLowerCase())
      : true;
    const matchConfidence = confidenceFilter
      ? conf.includes(confidenceFilter.toLowerCase())
      : true;

    return matchDrug && matchDisease && matchConfidence;
  });

  function applyServerFilter(event) {
    event.preventDefault();
    /* Find matching IDs from loaded lists */
    const matchedDrug = drugKeyword
      ? drugOptions.find((d) =>
          (d.tenThuoc || d.drugName || "")
            .toLowerCase()
            .includes(drugKeyword.toLowerCase())
        )
      : null;
    const matchedDisease = diseaseKeyword
      ? diseaseOptions.find((d) =>
          (d.tenBenh || d.diseaseName || "")
            .toLowerCase()
            .includes(diseaseKeyword.toLowerCase())
        )
      : null;

    setParams({
      thuocId: matchedDrug
        ? String(matchedDrug.thuocId || matchedDrug.drugId)
        : undefined,
      benhId: matchedDisease
        ? String(matchedDisease.benhId || matchedDisease.diseaseId)
        : undefined,
    });
  }

  function clearFilters() {
    setDrugKeyword("");
    setDiseaseKeyword("");
    setConfidenceFilter("");
    setParams({});
  }

  return (
    <section className="space-y-5">
      {/* Filter bar */}
      <Card className="!p-4">
        <form
          className="flex flex-col gap-3"
          onSubmit={applyServerFilter}
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <Input
              label="Tên thuốc"
              icon={Search}
              value={drugKeyword}
              onChange={(e) => setDrugKeyword(e.target.value)}
              placeholder="Ví dụ: Paracetamol..."
            />
            <Input
              label="Tên bệnh / chỉ định"
              icon={Search}
              value={diseaseKeyword}
              onChange={(e) => setDiseaseKeyword(e.target.value)}
              placeholder="Ví dụ: Đau đầu..."
            />
            <Select
              label="Mức tin cậy"
              value={confidenceFilter}
              onChange={(e) => setConfidenceFilter(e.target.value)}
            >
              <option value="">Tất cả mức tin cậy</option>
              {CONFIDENCE_LEVELS.map((lvl) => (
                <option key={lvl} value={lvl}>
                  {lvl}
                </option>
              ))}
            </Select>
          </div>

          <div className="flex gap-2">
            <Button type="submit" className="shrink-0">
              <Link2 size={16} />
              Tìm liên kết
            </Button>
            {(drugKeyword || diseaseKeyword || confidenceFilter || Object.keys(params).length > 0) && (
              <Button
                type="button"
                variant="ghost"
                size="md"
                onClick={clearFilters}
              >
                Xóa bộ lọc
              </Button>
            )}
          </div>
        </form>
      </Card>

      {state.error && (
        <Alert tone="danger">
          Không thể tải dữ liệu liên kết. Vui lòng kiểm tra kết nối Backend hoặc thử lại.
        </Alert>
      )}

      {state.loading ? (
        <LoadingSkeleton count={5} variant="row" />
      ) : items.length === 0 ? (
        <EmptyState icon={Link2} title="Chưa có liên kết phù hợp">
          {drugKeyword || diseaseKeyword || confidenceFilter
            ? "Không có dữ liệu phù hợp với bộ lọc hiện tại. Thử thay đổi tên thuốc hoặc bệnh/chỉ định."
            : "Nhập tên thuốc hoặc bệnh/chỉ định để tìm liên kết."}
        </EmptyState>
      ) : (
        <>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
            <span className="text-sm font-semibold text-slate-700">
              {items.length} liên kết đang hiển thị
            </span>
            <span className="text-xs text-slate-400">
              API giới hạn tối đa 100 dòng mỗi lần
            </span>
          </div>

          {/* Card-based table */}
          <div className="space-y-2.5">
            {items.map((link) => {
              const score = link.diemLienKet ?? link.sourceScore;
              const scoreNum = Number(score);
              const isFallbackScore =
                scoreNum === 0.65 &&
                (link.nguonDiem === "DATABASE_FALLBACK" || !link.nguonDiem);
              const scoreColor =
                scoreNum >= 0.7
                  ? "text-emerald-600"
                  : scoreNum >= 0.4
                    ? "text-blue-600"
                    : "text-slate-500";
              const barColor =
                scoreNum >= 0.7
                  ? "bg-emerald-500"
                  : scoreNum >= 0.4
                    ? "bg-blue-500"
                    : "bg-slate-400";

              return (
                <Card
                  key={link.lienKetId || link.linkId}
                  className="!p-4"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center gap-3">
                    {/* Drug → Disease */}
                    <div className="flex-1 min-w-0">
                      <strong className="block text-sm text-slate-900 line-clamp-1">
                        {link.tenThuoc || link.drugName}
                      </strong>
                      <span className="text-xs text-slate-500 line-clamp-1">
                        → {link.tenBenh || link.diseaseName}
                      </span>
                    </div>

                    {/* Badges */}
                    <div className="flex flex-wrap items-center gap-1.5 shrink-0">
                      {(link.tenLoaiLienKet || link.linkType) && (
                        <Badge tone="cyan">
                          {link.tenLoaiLienKet || link.linkType}
                        </Badge>
                      )}
                      {(link.tenMucTinCay || link.confidenceLevel) && (
                        <Badge tone="blue">
                          {link.tenMucTinCay || link.confidenceLevel}
                        </Badge>
                      )}
                      {isFallbackScore && (
                        <Badge tone="amber">Điểm mặc định</Badge>
                      )}
                      {link.nguonDiem === "AI_MODEL" && (
                        <Badge tone="emerald">AI Model</Badge>
                      )}
                    </div>

                    {/* Score */}
                    <div className="sm:w-20 text-right shrink-0">
                      <strong className={clsx("text-xl font-black tabular-nums", scoreColor)}>
                        {formatScore(score)}
                      </strong>
                      <div className="score-bar-track mt-1">
                        <div
                          className={`score-bar-fill ${barColor}`}
                          style={{
                            width: `${Math.round(Math.min(scoreNum * 100, 100))}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Evidence note */}
                  {(link.ghiChu || link.evidenceDescription || link.nguonBangChung) && (
                    <p className="text-xs text-slate-500 mt-2.5 m-0 line-clamp-2 leading-relaxed border-t border-slate-50 pt-2.5">
                      {truncate(
                        link.ghiChu || link.evidenceDescription || link.nguonBangChung,
                        200
                      )}
                    </p>
                  )}
                </Card>
              );
            })}
          </div>
        </>
      )}
    </section>
  );
}
