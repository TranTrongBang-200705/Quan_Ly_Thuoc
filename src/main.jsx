import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  Beaker,
  ClipboardList,
  Database,
  History,
  LayoutDashboard,
  Link2,
  MessageSquare,
  Pill,
  Search,
  Send,
  Settings,
  ShieldCheck,
  Stethoscope,
} from "lucide-react";
import { api } from "./api";
import "./styles.css";

const dieuHuongNguoiDung = [
  { id: "user-dashboard", label: "Tổng quan", icon: Activity },
  { id: "drugs", label: "Tra cứu thuốc", icon: Pill },
  { id: "diseases", label: "Tra cứu bệnh", icon: Stethoscope },
  { id: "links", label: "Liên kết đã biết", icon: Link2 },
  { id: "prediction", label: "Dự đoán", icon: Beaker },
  { id: "history", label: "Lịch sử dự đoán", icon: History },
  { id: "feedback", label: "Phản hồi", icon: MessageSquare },
];

const dieuHuongQuanTri = [
  { id: "admin-dashboard", label: "Tổng quan quản trị", icon: LayoutDashboard },
  { id: "admin-catalog", label: "Dữ liệu thuốc/bệnh", icon: Database },
  { id: "admin-links", label: "Liên kết thuốc-bệnh", icon: Link2 },
  { id: "admin-predictions", label: "Theo dõi dự đoán", icon: ClipboardList },
  { id: "admin-lookups", label: "Danh mục hệ thống", icon: Settings },
];

function useLoad(loader, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: "" });

  useEffect(() => {
    let active = true;
    setState((current) => ({ ...current, loading: true, error: "" }));
    loader()
      .then((data) => active && setState({ data, loading: false, error: "" }))
      .catch((error) =>
        active &&
        setState({
          data: null,
          loading: false,
          error: error.message || "Không tải được dữ liệu.",
        })
      );
    return () => {
      active = false;
    };
  }, deps);

  return state;
}

function App() {
  const [khuVuc, setKhuVuc] = useState("user");
  const [manHinh, setManHinh] = useState("user-dashboard");
  const danhSachDieuHuong = khuVuc === "user" ? dieuHuongNguoiDung : dieuHuongQuanTri;

  function doiKhuVuc(khuVucMoi) {
    setKhuVuc(khuVucMoi);
    setManHinh(khuVucMoi === "user" ? "user-dashboard" : "admin-dashboard");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">DD</span>
          <div>
            <strong>DrugDiseaseML</strong>
            <small>Giao diện kết nối backend</small>
          </div>
        </div>

        <div className="role-switcher" aria-label="Khu vực làm việc">
          <button className={khuVuc === "user" ? "active" : ""} onClick={() => doiKhuVuc("user")}>
            Người dùng
          </button>
          <button className={khuVuc === "admin" ? "active" : ""} onClick={() => doiKhuVuc("admin")}>
            Quản trị
          </button>
        </div>

        <nav>
          {danhSachDieuHuong.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={manHinh === item.id ? "nav-item active" : "nav-item"}
                onClick={() => setManHinh(item.id)}
                title={item.label}
              >
                <Icon size={18} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="content">
        {manHinh === "user-dashboard" && <TongQuanNguoiDung onOpen={setManHinh} />}
        {manHinh === "drugs" && <ManHinhThuoc />}
        {manHinh === "diseases" && <ManHinhBenh />}
        {manHinh === "links" && <ManHinhLienKet />}
        {manHinh === "prediction" && <ManHinhDuDoan />}
        {manHinh === "history" && <ManHinhLichSuDuDoan />}
        {manHinh === "feedback" && <ManHinhPhanHoi />}
        {manHinh === "admin-dashboard" && <TongQuanQuanTri onOpen={setManHinh} />}
        {manHinh === "admin-catalog" && <ManHinhQuanTriDanhMuc />}
        {manHinh === "admin-links" && <ManHinhQuanTriLienKet />}
        {manHinh === "admin-predictions" && <ManHinhQuanTriDuDoan />}
        {manHinh === "admin-lookups" && <ManHinhQuanTriLookup />}
      </main>
    </div>
  );
}

function TongQuanNguoiDung({ onOpen }) {
  const lookups = useLoad(() => api.getLookups(), []);
  const lichSu = useLoad(() => api.getPredictionHistory(), []);

  const cards = [
    { label: "Loại dự đoán", value: lookups.data?.predictionTypes?.length ?? "-", hint: "Từ /api/lookups" },
    { label: "Mức tin cậy", value: lookups.data?.confidenceLevels?.length ?? "-", hint: "Bảng ConfidenceLevels" },
    { label: "Loại liên kết", value: lookups.data?.linkTypes?.length ?? "-", hint: "Bảng LinkTypes" },
    { label: "Lịch sử dự đoán", value: lichSu.data?.length ?? "-", hint: "Từ /api/predictions/history" },
  ];

  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Khu vực người dùng"
        title="Dự đoán liên kết thuốc - bệnh"
        subtitle="Tra cứu dữ liệu, gửi yêu cầu dự đoán và phản hồi kết quả dựa trên backend hiện có."
      />
      <LuoiChiSo cards={cards} />
      <div className="action-grid">
        <button className="feature-button" onClick={() => onOpen("drugs")}>
          <Pill size={20} />
          Tra cứu thuốc
        </button>
        <button className="feature-button" onClick={() => onOpen("diseases")}>
          <Stethoscope size={20} />
          Tra cứu bệnh
        </button>
        <button className="feature-button" onClick={() => onOpen("prediction")}>
          <Beaker size={20} />
          Tạo yêu cầu dự đoán
        </button>
      </div>
    </section>
  );
}

function TongQuanQuanTri({ onOpen }) {
  const thuoc = useLoad(() => api.getDrugs({ take: 100 }), []);
  const benh = useLoad(() => api.getDiseases({ take: 100 }), []);
  const lienKet = useLoad(() => api.getLinks({}), []);
  const lichSu = useLoad(() => api.getPredictionHistory(), []);
  const lookups = useLoad(() => api.getLookups(), []);

  const cards = [
    { label: "Thuốc đang hiển thị", value: thuoc.data?.length ?? "-", hint: "Backend cho lấy tối đa 100/lần" },
    { label: "Bệnh đang hiển thị", value: benh.data?.length ?? "-", hint: "Backend cho lấy tối đa 100/lần" },
    { label: "Liên kết đang hiển thị", value: lienKet.data?.length ?? "-", hint: "Backend giới hạn 100 dòng" },
    { label: "Yêu cầu dự đoán", value: lichSu.data?.length ?? "-", hint: "Từ /api/predictions/history" },
  ];

  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Khu vực quản trị"
        title="Giám sát vận hành backend"
        subtitle="Các màn hình quản trị hiện là chế độ đọc/giám sát theo những API đã có."
      />
      <LuoiChiSo cards={cards} />
      <GhiChuQuanTri>
        API hiện tại hỗ trợ đọc/tìm kiếm dữ liệu và tạo prediction/feedback. Các chức năng thêm, sửa, xóa, duyệt,
        triển khai model và audit log cần bổ sung endpoint backend trước khi giao diện có thể ghi dữ liệu.
      </GhiChuQuanTri>
      <div className="action-grid">
        <button className="feature-button" onClick={() => onOpen("admin-catalog")}>
          <Database size={20} />
          Giám sát thuốc/bệnh
        </button>
        <button className="feature-button" onClick={() => onOpen("admin-links")}>
          <Link2 size={20} />
          Xem liên kết
        </button>
        <button className="feature-button" onClick={() => onOpen("admin-predictions")}>
          <ClipboardList size={20} />
          Theo dõi dự đoán
        </button>
      </div>
      <TomTatLookup lookups={lookups} />
    </section>
  );
}

function ManHinhThuoc({ title = "Tra cứu thuốc", subtitle = "Hiển thị tối đa 100 dòng/lần do backend đang giới hạn take." }) {
  const [tuKhoa, setTuKhoa] = useState("");
  const [truyVan, setTruyVan] = useState("");
  const [soDong, setSoDong] = useState(100);
  const { data, loading, error } = useLoad(
    () => api.getDrugs({ keyword: truyVan, take: soDong }),
    [truyVan, soDong]
  );

  return (
    <section className="page">
      <TieuDeTrang title={title} subtitle={subtitle} />
      <ThanhTimKiem
        value={tuKhoa}
        onChange={setTuKhoa}
        onSearch={() => setTruyVan(tuKhoa)}
        soDong={soDong}
        onLimitChange={setSoDong}
      />
      <ThongTinGioiHan hienThi={data?.length} tong="597" loai="thuốc" />
      <TrangThaiDuLieu loading={loading} error={error}>
        <table>
          <thead>
            <tr>
              <th>DrugId</th>
              <th>Mã thuốc</th>
              <th>Hoạt chất</th>
              <th>Tên thương mại</th>
              <th>Chỉ định đã biết</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((drug) => (
              <tr key={drug.drugId}>
                <td>{drug.drugId}</td>
                <td>{drug.drugCode}</td>
                <td>{drug.activeName}</td>
                <td>{drug.tradeName || "-"}</td>
                <td className="muted">{drug.knownIndications || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TrangThaiDuLieu>
    </section>
  );
}

function ManHinhBenh({ title = "Tra cứu bệnh", subtitle = "Hiển thị tối đa 100 dòng/lần do backend đang giới hạn take." }) {
  const [tuKhoa, setTuKhoa] = useState("");
  const [truyVan, setTruyVan] = useState("");
  const [soDong, setSoDong] = useState(100);
  const { data, loading, error } = useLoad(
    () => api.getDiseases({ keyword: truyVan, take: soDong }),
    [truyVan, soDong]
  );

  return (
    <section className="page">
      <TieuDeTrang title={title} subtitle={subtitle} />
      <ThanhTimKiem
        value={tuKhoa}
        onChange={setTuKhoa}
        onSearch={() => setTruyVan(tuKhoa)}
        soDong={soDong}
        onLimitChange={setSoDong}
      />
      <ThongTinGioiHan hienThi={data?.length} tong="71" loai="bệnh" />
      <TrangThaiDuLieu loading={loading} error={error}>
        <table>
          <thead>
            <tr>
              <th>DiseaseId</th>
              <th>Mã bệnh</th>
              <th>Tên bệnh</th>
              <th>Mô tả</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((disease) => (
              <tr key={disease.diseaseId}>
                <td>{disease.diseaseId}</td>
                <td>{disease.diseaseCode}</td>
                <td>{disease.diseaseName}</td>
                <td className="muted">{disease.description || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TrangThaiDuLieu>
    </section>
  );
}

function ManHinhLienKet({
  title = "Liên kết thuốc - bệnh đã biết",
  subtitle = "Backend hiện trả tối đa 100 liên kết/lần. Hãy lọc bằng DrugId hoặc DiseaseId để xem đúng nhóm cần tìm.",
}) {
  const [drugId, setDrugId] = useState("");
  const [diseaseId, setDiseaseId] = useState("");
  const [params, setParams] = useState({});
  const { data, loading, error } = useLoad(() => api.getLinks(params), [JSON.stringify(params)]);

  return (
    <section className="page">
      <TieuDeTrang title={title} subtitle={subtitle} />
      <div className="filters">
        <label>
          DrugId
          <input value={drugId} onChange={(event) => setDrugId(event.target.value)} />
        </label>
        <label>
          DiseaseId
          <input value={diseaseId} onChange={(event) => setDiseaseId(event.target.value)} />
        </label>
        <button
          className="primary"
          onClick={() =>
            setParams({
              drugId: drugId ? Number(drugId) : undefined,
              diseaseId: diseaseId ? Number(diseaseId) : undefined,
            })
          }
        >
          <Search size={16} />
          Lọc
        </button>
      </div>
      <ThongTinGioiHan hienThi={data?.length} tong="4,600" loai="liên kết" />
      <TrangThaiDuLieu loading={loading} error={error}>
        <table>
          <thead>
            <tr>
              <th>DrugId</th>
              <th>Thuốc</th>
              <th>DiseaseId</th>
              <th>Bệnh</th>
              <th>Điểm</th>
              <th>Mức tin cậy</th>
              <th>Bằng chứng</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((link) => (
              <tr key={link.linkId}>
                <td>{link.drugId}</td>
                <td>{link.drugName}</td>
                <td>{link.diseaseId}</td>
                <td>{link.diseaseName}</td>
                <td>{formatScore(link.sourceScore)}</td>
                <td>{link.confidenceLevel || "-"}</td>
                <td className="muted">{link.evidenceDescription || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TrangThaiDuLieu>
    </section>
  );
}

function ManHinhQuanTriDanhMuc() {
  const [tab, setTab] = useState("drugs");
  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Quản trị"
        title="Giám sát dữ liệu thuốc và bệnh"
        subtitle="Backend hiện hỗ trợ đọc/tìm kiếm Drugs và Diseases."
      />
      <div className="tabs">
        <button className={tab === "drugs" ? "active" : ""} onClick={() => setTab("drugs")}>
          Thuốc
        </button>
        <button className={tab === "diseases" ? "active" : ""} onClick={() => setTab("diseases")}>
          Bệnh
        </button>
      </div>
      <GhiChuQuanTri>
        Màn hình thêm/sửa/xóa cần API ghi dữ liệu như POST, PUT, PATCH hoặc DELETE ở backend.
      </GhiChuQuanTri>
      {tab === "drugs" ? (
        <ManHinhThuoc title="Danh mục thuốc" subtitle="Chế độ đọc: GET /api/drugs" />
      ) : (
        <ManHinhBenh title="Danh mục bệnh" subtitle="Chế độ đọc: GET /api/diseases" />
      )}
    </section>
  );
}

function ManHinhQuanTriLienKet() {
  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Quản trị"
        title="Giám sát liên kết thuốc - bệnh"
        subtitle="Backend hiện hỗ trợ lọc liên kết bằng DrugId và DiseaseId."
      />
      <GhiChuQuanTri>
        Chức năng duyệt/chấm điểm/chỉnh sửa liên kết cần endpoint backend riêng trước khi giao diện có thể ghi database.
      </GhiChuQuanTri>
      <ManHinhLienKet title="Liên kết đã biết" subtitle="Chế độ đọc: GET /api/links" />
    </section>
  );
}

function ManHinhQuanTriDuDoan() {
  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Quản trị"
        title="Theo dõi yêu cầu dự đoán"
        subtitle="Backend hiện cung cấp lịch sử dự đoán để theo dõi trạng thái và số kết quả."
      />
      <GhiChuQuanTri>Retry, hủy run, triển khai model và audit chi tiết chưa có API backend.</GhiChuQuanTri>
      <ManHinhLichSuDuDoan title="Tất cả yêu cầu dự đoán" subtitle="Chế độ đọc: GET /api/predictions/history" />
    </section>
  );
}

function ManHinhQuanTriLookup() {
  return (
    <section className="page">
      <TieuDeTrang
        eyebrow="Quản trị"
        title="Danh mục hệ thống"
        subtitle="Backend hiện cung cấp PredictionTypes, ConfidenceLevels và LinkTypes."
      />
      <GhiChuQuanTri>Chỉnh sửa lookup cần API ghi dữ liệu. Màn hình này dùng để kiểm tra giá trị đang được backend dùng.</GhiChuQuanTri>
      <ManHinhLookup />
    </section>
  );
}

function ManHinhDuDoan() {
  const lookups = useLoad(() => api.getLookups(), []);
  const [request, setRequest] = useState({
    predictionType: "DRUG_TO_DISEASE",
    drugId: "",
    diseaseId: "",
    topK: 10,
    scoreThreshold: 0.5,
    purpose: "Nghiên cứu liên kết thuốc - bệnh",
    contactEmail: "",
    medicalWarningAccepted: true,
  });
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const predictionTypes = lookups.data?.predictionTypes ?? [
    { code: "DRUG_TO_DISEASE", name: "Từ thuốc tìm bệnh" },
    { code: "DISEASE_TO_DRUG", name: "Từ bệnh tìm thuốc" },
    { code: "PAIR_PREDICTION", name: "Dự đoán một cặp thuốc - bệnh" },
  ];

  const update = (key, value) => setRequest((current) => ({ ...current, [key]: value }));

  async function submit(event) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    setResponse(null);
    try {
      const payload = {
        ...request,
        drugId: request.drugId ? Number(request.drugId) : null,
        diseaseId: request.diseaseId ? Number(request.diseaseId) : null,
        topK: Number(request.topK),
        scoreThreshold: Number(request.scoreThreshold),
      };
      setResponse(await api.createPrediction(payload));
    } catch (err) {
      setError(err.message || "Không tạo được yêu cầu dự đoán.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="page two-column">
      <div>
        <TieuDeTrang title="Tạo yêu cầu dự đoán" subtitle="POST /api/predictions" />
        <form className="panel form-grid" onSubmit={submit}>
          <label>
            Loại dự đoán
            <select value={request.predictionType} onChange={(event) => update("predictionType", event.target.value)}>
              {predictionTypes.map((type) => (
                <option key={type.code} value={type.code}>
                  {type.code} - {type.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            DrugId
            <input type="number" value={request.drugId} onChange={(event) => update("drugId", event.target.value)} />
          </label>
          <label>
            DiseaseId
            <input type="number" value={request.diseaseId} onChange={(event) => update("diseaseId", event.target.value)} />
          </label>
          <label>
            TopK
            <input type="number" min="1" max="100" value={request.topK} onChange={(event) => update("topK", event.target.value)} />
          </label>
          <label>
            Ngưỡng điểm
            <input
              type="number"
              min="0"
              max="1"
              step="0.01"
              value={request.scoreThreshold}
              onChange={(event) => update("scoreThreshold", event.target.value)}
            />
          </label>
          <label>
            Email liên hệ
            <input type="email" value={request.contactEmail} onChange={(event) => update("contactEmail", event.target.value)} />
          </label>
          <label className="wide">
            Mục đích
            <textarea value={request.purpose} onChange={(event) => update("purpose", event.target.value)} />
          </label>
          <label className="checkbox wide">
            <input
              type="checkbox"
              checked={request.medicalWarningAccepted}
              onChange={(event) => update("medicalWarningAccepted", event.target.checked)}
            />
            Tôi xác nhận kết quả chỉ dùng để hỗ trợ tham khảo, không thay thế tư vấn y khoa.
          </label>
          {error && <p className="error wide">{error}</p>}
          <button className="primary wide" disabled={submitting}>
            <Send size={16} />
            {submitting ? "Đang gửi..." : "Gửi yêu cầu dự đoán"}
          </button>
        </form>
      </div>

      <BangKetQuaDuDoan response={response} />
    </section>
  );
}

function BangKetQuaDuDoan({ response }) {
  if (!response) {
    return (
      <aside className="panel empty-panel">
        <ClipboardList size={32} />
        <h3>Kết quả dự đoán</h3>
        <p>Backend sẽ trả về mã request, mã run và danh sách kết quả xếp hạng tại đây.</p>
      </aside>
    );
  }

  return (
    <aside className="panel">
      <h3>{response.requestCode}</h3>
      <p className="muted">Run: {response.runCode || response.predictionRunId}</p>
      <span className="status">{response.requestStatus}</span>
      <div className="result-list">
        {(response.results ?? []).map((result) => (
          <article key={result.predictionResultId} className="result-item">
            <strong>
              #{result.rankNo} {result.drugName} → {result.diseaseName}
            </strong>
            <span>{formatScore(result.predictionScore)}</span>
            <small>
              {result.confidenceLevel || "Không rõ"} - {result.linkType || "Chưa phân loại"}
            </small>
            <p>{result.explanationText}</p>
          </article>
        ))}
      </div>
    </aside>
  );
}

function ManHinhLichSuDuDoan({ title = "Lịch sử dự đoán", subtitle = "GET /api/predictions/history" }) {
  const { data, loading, error } = useLoad(() => api.getPredictionHistory(), []);
  return (
    <section className="page">
      <TieuDeTrang title={title} subtitle={subtitle} />
      <TrangThaiDuLieu loading={loading} error={error}>
        <table>
          <thead>
            <tr>
              <th>Mã request</th>
              <th>Loại</th>
              <th>Thuốc</th>
              <th>Bệnh</th>
              <th>Trạng thái</th>
              <th>Số kết quả</th>
            </tr>
          </thead>
          <tbody>
            {(data ?? []).map((item) => (
              <tr key={item.requestId}>
                <td>{item.requestCode}</td>
                <td>{item.predictionType}</td>
                <td>{item.inputDrugName || "-"}</td>
                <td>{item.inputDiseaseName || "-"}</td>
                <td><span className="status">{item.requestStatus}</span></td>
                <td>{item.resultCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </TrangThaiDuLieu>
    </section>
  );
}

function ManHinhPhanHoi() {
  const [form, setForm] = useState({
    predictionRunId: "",
    predictionResultId: "",
    userId: "",
    generalAssessment: "Hợp lý",
    usefulScore: 5,
    suggestedAction: "Giữ kết quả",
    reasonText: "",
  });
  const [response, setResponse] = useState(null);
  const [error, setError] = useState("");

  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  async function submit(event) {
    event.preventDefault();
    setError("");
    setResponse(null);
    try {
      const payload = {
        ...form,
        predictionRunId: Number(form.predictionRunId),
        predictionResultId: form.predictionResultId ? Number(form.predictionResultId) : null,
        userId: form.userId ? Number(form.userId) : null,
        usefulScore: form.usefulScore ? Number(form.usefulScore) : null,
      };
      setResponse(await api.createFeedback(payload));
    } catch (err) {
      setError(err.message || "Không gửi được phản hồi.");
    }
  }

  return (
    <section className="page">
      <TieuDeTrang title="Gửi phản hồi" subtitle="POST /api/feedbacks" />
      <form className="panel form-grid" onSubmit={submit}>
        <label>
          PredictionRunId
          <input type="number" required value={form.predictionRunId} onChange={(event) => update("predictionRunId", event.target.value)} />
        </label>
        <label>
          PredictionResultId
          <input type="number" value={form.predictionResultId} onChange={(event) => update("predictionResultId", event.target.value)} />
        </label>
        <label>
          UserId
          <input type="number" value={form.userId} onChange={(event) => update("userId", event.target.value)} />
        </label>
        <label>
          Đánh giá
          <input required value={form.generalAssessment} onChange={(event) => update("generalAssessment", event.target.value)} />
        </label>
        <label>
          Điểm hữu ích
          <input type="number" min="1" max="5" value={form.usefulScore} onChange={(event) => update("usefulScore", event.target.value)} />
        </label>
        <label>
          Hành động đề xuất
          <input value={form.suggestedAction} onChange={(event) => update("suggestedAction", event.target.value)} />
        </label>
        <label className="wide">
          Lý do
          <textarea value={form.reasonText} onChange={(event) => update("reasonText", event.target.value)} />
        </label>
        {error && <p className="error wide">{error}</p>}
        {response && <p className="success wide">Đã tạo phản hồi {response.feedbackCode} với ID {response.feedbackId}.</p>}
        <button className="primary wide">
          <MessageSquare size={16} />
          Gửi phản hồi
        </button>
      </form>
    </section>
  );
}

function ManHinhLookup() {
  const { data, loading, error } = useLoad(() => api.getLookups(), []);
  return (
    <section className="page">
      <TieuDeTrang title="Danh mục backend" subtitle="GET /api/lookups" />
      <TrangThaiDuLieu loading={loading} error={error}>
        <NhomLookup data={data} />
      </TrangThaiDuLieu>
    </section>
  );
}

function TomTatLookup({ lookups }) {
  if (lookups.loading) return <div className="panel state">Đang tải danh mục...</div>;
  if (lookups.error) return <div className="panel state error">{lookups.error}</div>;
  return (
    <div className="panel">
      <h3>Danh mục backend đang dùng</h3>
      <NhomLookup data={lookups.data} />
    </div>
  );
}

function NhomLookup({ data }) {
  const groups = useMemo(
    () => [
      ["Loại dự đoán", data?.predictionTypes ?? []],
      ["Mức tin cậy", data?.confidenceLevels ?? []],
      ["Loại liên kết", data?.linkTypes ?? []],
    ],
    [data]
  );

  return (
    <div className="lookup-grid">
      {groups.map(([title, items]) => (
        <article className="panel compact-panel" key={title}>
          <h3>{title}</h3>
          <ul className="lookup-list">
            {items.map((item) => (
              <li key={item.id}>
                <code>{item.code}</code>
                <span>{item.name}</span>
              </li>
            ))}
          </ul>
        </article>
      ))}
    </div>
  );
}

function LuoiChiSo({ cards }) {
  return (
    <div className="metric-grid">
      {cards.map((card) => (
        <article className="metric-card" key={card.label}>
          <span>{card.label}</span>
          <strong>{card.value}</strong>
          <small>{card.hint}</small>
        </article>
      ))}
    </div>
  );
}

function TieuDeTrang({ eyebrow, title, subtitle }) {
  return (
    <header className="page-title">
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  );
}

function ThanhTimKiem({ value, onChange, onSearch, soDong, onLimitChange }) {
  return (
    <div className="search-bar">
      <Search size={18} />
      <input
        value={value}
        placeholder="Nhập từ khóa..."
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => event.key === "Enter" && onSearch()}
      />
      <label className="limit-select">
        Số dòng
        <select value={soDong} onChange={(event) => onLimitChange(Number(event.target.value))}>
          <option value={20}>20</option>
          <option value={50}>50</option>
          <option value={100}>100</option>
        </select>
      </label>
      <button className="primary" onClick={onSearch}>Tìm</button>
    </div>
  );
}

function ThongTinGioiHan({ hienThi, tong, loai }) {
  return (
    <div className="data-hint">
      Đang hiển thị {hienThi ?? 0} / {tong} {loai}. Backend hiện chưa có phân trang offset/page, nên mỗi lần chỉ lấy tối đa 100 dòng.
    </div>
  );
}

function GhiChuQuanTri({ children }) {
  return (
    <div className="admin-note">
      <ShieldCheck size={20} />
      <p>{children}</p>
    </div>
  );
}

function TrangThaiDuLieu({ loading, error, children }) {
  if (loading) return <div className="panel state">Đang tải dữ liệu...</div>;
  if (error) return <div className="panel state error">{error}</div>;
  return <div className="table-wrap">{children}</div>;
}

function formatScore(value) {
  if (value === null || value === undefined || value === "") return "-";
  return Number(value).toFixed(4);
}

createRoot(document.getElementById("root")).render(<App />);
