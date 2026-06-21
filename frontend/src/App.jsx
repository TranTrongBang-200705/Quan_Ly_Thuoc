import {
  Activity,
  Beaker,
  History,
  MessageSquare,
  Search,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import toast from "react-hot-toast";
import { api, clearStoredAuth, getStoredAuth, saveStoredAuth } from "./api";
import { AppLayout } from "./components/layout";
import { LoadingSkeleton } from "./components/ui";
import { AuthPage } from "./pages/AuthPage";
import { CatalogPage } from "./pages/CatalogPages";
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
  catalog: {
    title: "Tra cứu thuốc/bệnh",
    subtitle: "Catalog thuốc, bệnh/chỉ định, tìm kiếm và xem chi tiết dữ liệu y dược.",
    eyebrow: "Medical catalog",
  },
  prediction: {
    title: "Dự đoán liên kết thuốc-bệnh bằng AI",
    subtitle: "Mô hình RandomForest chấm điểm khả năng liên kết giữa thuốc và bệnh/chỉ định từ dữ liệu huấn luyện.",
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
};

const ADMIN_FEEDBACK_META = {
  title: "Quản lý phản hồi",
  subtitle: "Theo dõi phản hồi của người dùng về kết quả dự đoán.",
  eyebrow: "Feedback admin",
};

const USER_NAV = [
  { id: "dashboard", label: "Tổng quan", icon: Activity },
  { id: "catalog", label: "Tra cứu thuốc/bệnh", icon: Search },
  { id: "prediction", label: "Dự đoán AI", icon: Beaker },
  { id: "history", label: "Lịch sử", icon: History },
  { id: "feedback", label: "Phản hồi", icon: MessageSquare },
];

const USER_PAGE_IDS = new Set(USER_NAV.map((item) => item.id));
const LEGACY_ADMIN_PAGE_IDS = new Set([
  "admin-dashboard",
  "admin-links",
  "admin-predictions",
  "admin-lookups",
  "admin-catalog",
  "links",
]);

function readPageFromHash() {
  if (typeof window === "undefined") return "dashboard";
  const raw = window.location.hash.replace(/^#\/?/, "").trim();
  if (raw) return raw;
  const pathPage = window.location.pathname.replace(/^\/+/, "").split("/")[0];
  return pathPage || "dashboard";
}

function pageIdOnly(pageId) {
  return String(pageId || "").split("?")[0];
}

function catalogTabFromPage(pageId) {
  const value = String(pageId || "").toLowerCase();
  return value.includes("disease") || value.includes("benh") || value.includes("tab=diseases")
    ? "diseases"
    : "drugs";
}

function roleName(role) {
  if (typeof role === "string") return role;
  return role?.roleCode || role?.code || role?.name || role?.role || "";
}

export default function App() {
  const [auth, setAuth] = useState(() => getStoredAuth());
  const [authChecked, setAuthChecked] = useState(false);
  const [activePage, setActivePage] = useState(() => readPageFromHash());
  const [catalogInitialTab, setCatalogInitialTab] = useState(() =>
    catalogTabFromPage(readPageFromHash()),
  );
  const [health, setHealth] = useState(null);
  const healthToastRef = useRef({ backend: false, ai: false });

  const user = auth?.user;
  const roles = useMemo(
    () => (user?.roles ?? []).map(roleName).filter(Boolean),
    [user?.roles],
  );
  const isAdmin =
    roles.some((role) => role.toUpperCase() === "ADMIN") ||
    user?.isAdmin === true ||
    user?.admin === true;

  const normalizePageForRole = useCallback((pageId) => {
    const basePageId = pageIdOnly(pageId);
    if (basePageId === "drugs" || basePageId === "diseases") return "catalog";
    if (LEGACY_ADMIN_PAGE_IDS.has(basePageId) || basePageId.startsWith("admin-")) {
      return "dashboard";
    }
    if (USER_PAGE_IDS.has(basePageId)) return basePageId;
    return "dashboard";
  }, []);

  const navigate = useCallback(
    (pageId) => {
      const nextPage = normalizePageForRole(pageId);
      if (nextPage === "catalog") {
        setCatalogInitialTab(catalogTabFromPage(pageId));
      }
      setActivePage(nextPage);
      if (typeof window !== "undefined" && window.location.hash !== `#${nextPage}`) {
        window.history.replaceState(null, "", `#${nextPage}`);
      }
    },
    [normalizePageForRole],
  );

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

  const navItems = useMemo(
    () => [{ label: "Điều hướng chính", items: USER_NAV }],
    [],
  );

  const currentPageMeta = useMemo(() => {
    if (activePage === "feedback" && isAdmin) return ADMIN_FEEDBACK_META;
    return PAGE_META[activePage] || PAGE_META.dashboard;
  }, [activePage, isAdmin]);

  useEffect(() => {
    const nextPage = normalizePageForRole(activePage);
    if (nextPage !== activePage) {
      navigate(nextPage);
    }
  }, [activePage, navigate, normalizePageForRole]);

  useEffect(() => {
    function syncHashPage() {
      navigate(readPageFromHash());
    }

    syncHashPage();
    window.addEventListener("hashchange", syncHashPage);
    return () => window.removeEventListener("hashchange", syncHashPage);
  }, [navigate]);

  function logout() {
    clearStoredAuth();
    setAuth(null);
    navigate("dashboard");
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
          navigate("dashboard");
        }}
      />
    );
  }

  function renderPage() {
    switch (activePage) {
      case "dashboard":
        return <DashboardPage onNavigate={navigate} health={health} />;
      case "catalog":
        return <CatalogPage initialTab={catalogInitialTab} />;
      case "prediction":
        return <PredictionPage user={user} health={health} />;
      case "history":
        return <HistoryPage />;
      case "feedback":
        return <FeedbackPage user={user} roles={roles} isAdmin={isAdmin} />;
      default:
        return <DashboardPage onNavigate={navigate} health={health} />;
    }
  }

  return (
    <AppLayout
      navItems={navItems}
      activePage={activePage}
      pageMeta={currentPageMeta}
      onNavigate={navigate}
      user={user}
      roles={roles}
      onLogout={logout}
      health={health}
    >
      {renderPage()}
    </AppLayout>
  );
}
