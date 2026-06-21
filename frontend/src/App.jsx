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
  Settings,
  Stethoscope,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { api, clearStoredAuth, getStoredAuth, saveStoredAuth } from "./api";
import { AppLayout } from "./components/layout";
import { Alert, LoadingSkeleton } from "./components/ui";
import { AdminCatalogPage, AdminDashboardPage, AdminLookupsPage } from "./pages/AdminPages";
import { AuthPage } from "./pages/AuthPage";
import { DiseasesPage, DrugsPage, LinksPage } from "./pages/CatalogPages";
import { DashboardPage } from "./pages/DashboardPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { HistoryPage } from "./pages/HistoryPage";
import { PredictionPage } from "./pages/PredictionPage";

const PAGE_META = {
  dashboard: {
    title: "Tổng quan",
    subtitle: "Clinical intelligence dashboard cho dữ liệu thuốc-bệnh.",
    eyebrow: "Medical AI",
  },
  drugs: {
    title: "Tra cứu thuốc",
    subtitle: "Catalog thuốc, hoạt chất, công dụng, ảnh và thông tin an toàn.",
    eyebrow: "Drug discovery",
  },
  diseases: {
    title: "Tra cứu bệnh/chỉ định",
    subtitle: "Clinical indications, nhóm bệnh và mô tả liên quan.",
    eyebrow: "Disease knowledge",
  },
  links: {
    title: "Liên kết thuốc-bệnh",
    subtitle: "Evidence graph giữa thuốc, bệnh, loại liên kết và mức tin cậy.",
    eyebrow: "Evidence graph",
  },
  prediction: {
    title: "Dự đoán AI",
    subtitle: "Phân tích liên kết thuốc-bệnh bằng AI và dữ liệu DataThuoc.",
    eyebrow: "AI workflow",
  },
  history: {
    title: "Lịch sử dự đoán",
    subtitle: "Theo dõi request, trạng thái và kết quả đã lưu.",
    eyebrow: "Audit trail",
  },
  feedback: {
    title: "Phản hồi",
    subtitle: "Gửi đánh giá để cải thiện chất lượng dự đoán.",
    eyebrow: "Feedback loop",
  },
  "admin-dashboard": {
    title: "Tổng quan quản trị",
    subtitle: "Giám sát dữ liệu, liên kết và hoạt động dự đoán.",
    eyebrow: "Admin",
  },
  "admin-catalog": {
    title: "Dữ liệu thuốc/bệnh",
    subtitle: "Kiểm tra nhanh catalog DataThuoc.",
    eyebrow: "Admin catalog",
  },
  "admin-links": {
    title: "Quản trị liên kết",
    subtitle: "Theo dõi liên kết thuốc-bệnh theo bộ lọc.",
    eyebrow: "Admin evidence",
  },
  "admin-predictions": {
    title: "Theo dõi dự đoán",
    subtitle: "Giám sát các yêu cầu dự đoán trong hệ thống.",
    eyebrow: "Admin monitoring",
  },
  "admin-lookups": {
    title: "Danh mục hệ thống",
    subtitle: "Lookup phục vụ nghiệp vụ và form lâm sàng.",
    eyebrow: "Taxonomy",
  },
};

const USER_NAV = [
  { id: "dashboard", label: "Tổng quan", icon: Activity },
  { id: "drugs", label: "Tra cứu thuốc", icon: Pill },
  { id: "diseases", label: "Bệnh/chỉ định", icon: Stethoscope },
  { id: "links", label: "Liên kết", icon: Link2 },
  { id: "prediction", label: "Dự đoán AI", icon: Beaker },
  { id: "history", label: "Lịch sử", icon: History },
  { id: "feedback", label: "Phản hồi", icon: MessageSquare },
];

const ADMIN_NAV = [
  { id: "admin-dashboard", label: "Tổng quan quản trị", icon: LayoutDashboard },
  { id: "admin-catalog", label: "Dữ liệu thuốc/bệnh", icon: Database },
  { id: "admin-links", label: "Quản trị liên kết", icon: Link2 },
  { id: "admin-predictions", label: "Theo dõi dự đoán", icon: ClipboardList },
  { id: "admin-lookups", label: "Danh mục hệ thống", icon: Settings },
];

export default function App() {
  const [auth, setAuth] = useState(() => getStoredAuth());
  const [authChecked, setAuthChecked] = useState(false);
  const [activePage, setActivePage] = useState("dashboard");
  const [health, setHealth] = useState(null);
  const healthToastRef = useRef({ backend: false, ai: false });

  const user = auth?.user;
  const roles = user?.roles ?? [];
  const isAdmin = roles.includes("ADMIN");

  useEffect(() => {
    async function verifySession() {
      if (!auth?.accessToken) {
        setAuthChecked(true);
        return;
      }

      try {
        const currentUser = await api.me();
        const nextAuth = { ...auth, user: currentUser };
        saveStoredAuth(nextAuth);
        setAuth(nextAuth);
      } catch {
        clearStoredAuth();
        setAuth(null);
      } finally {
        setAuthChecked(true);
      }
    }

    verifySession();
  }, []);

  useEffect(() => {
    if (!authChecked) return undefined;
    let active = true;

    async function loadHealth() {
      try {
        const data = await api.getHealth();
        if (active) {
          setHealth(data);
          if (data?.aiStatus === "unavailable" && !healthToastRef.current.ai) {
            toast("AI service chưa khả dụng. Hệ thống sẽ ưu tiên dữ liệu liên kết dự phòng khi cần.", {
              icon: "AI",
            });
            healthToastRef.current.ai = true;
          }
        }
      } catch {
        if (active) {
          setHealth({ status: "offline", aiStatus: "unavailable" });
          if (!healthToastRef.current.backend) {
            toast.error("Backend không kết nối. Vui lòng kiểm tra dịch vụ API hoặc cấu hình VITE_API_BASE_URL.");
            healthToastRef.current.backend = true;
          }
        }
      }
    }

    loadHealth();
    const timer = window.setInterval(loadHealth, 45000);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [authChecked, auth?.accessToken]);

  const navItems = useMemo(() => {
    const groups = [{ label: "Clinical workspace", items: USER_NAV }];
    if (isAdmin) groups.push({ label: "Administration", items: ADMIN_NAV });
    return groups;
  }, [isAdmin]);

  useEffect(() => {
    if (!isAdmin && activePage.startsWith("admin-")) {
      setActivePage("dashboard");
    }
  }, [isAdmin, activePage]);

  function logout() {
    clearStoredAuth();
    setAuth(null);
    setActivePage("dashboard");
  }

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSkeleton count={1} />
      </div>
    );
  }

  if (!auth) {
    return (
      <AuthPage
        onAuthenticated={(result) => {
          saveStoredAuth(result);
          setAuth(result);
          setActivePage("dashboard");
        }}
      />
    );
  }

  function renderPage() {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={setActivePage} health={health} />;
      case "drugs":
        return <DrugsPage />;
      case "diseases":
        return <DiseasesPage />;
      case "links":
        return <LinksPage />;
      case "prediction":
        return <PredictionPage user={user} health={health} />;
      case "history":
        return <HistoryPage />;
      case "feedback":
        return <FeedbackPage user={user} />;
      case "admin-dashboard":
        return isAdmin ? <AdminDashboardPage /> : <Alert tone="danger">Bạn không có quyền truy cập trang quản trị.</Alert>;
      case "admin-catalog":
        return isAdmin ? <AdminCatalogPage /> : <Alert tone="danger">Bạn không có quyền truy cập trang quản trị.</Alert>;
      case "admin-links":
        return isAdmin ? <LinksPage admin /> : <Alert tone="danger">Bạn không có quyền truy cập trang quản trị.</Alert>;
      case "admin-predictions":
        return isAdmin ? <HistoryPage admin /> : <Alert tone="danger">Bạn không có quyền truy cập trang quản trị.</Alert>;
      case "admin-lookups":
        return isAdmin ? <AdminLookupsPage /> : <Alert tone="danger">Bạn không có quyền truy cập trang quản trị.</Alert>;
      default:
        return <DashboardPage onNavigate={setActivePage} health={health} />;
    }
  }

  return (
    <AppLayout
      navItems={navItems}
      activePage={activePage}
      pageMeta={PAGE_META[activePage] || PAGE_META.dashboard}
      onNavigate={setActivePage}
      user={user}
      roles={roles}
      onLogout={logout}
      health={health}
    >
      {renderPage()}
    </AppLayout>
  );
}
