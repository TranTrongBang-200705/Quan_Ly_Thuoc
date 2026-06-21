import { Menu, Search, UserRound } from "lucide-react";
import { SystemStatusBadge } from "../medical";

export function Topbar({ page, user, health, onMenuClick }) {
  const backendStatus = health?.status === "healthy" ? "online" : "offline";
  const databaseStatus = health?.status === "healthy" ? "healthy" : "unknown";
  const aiStatus = health?.aiStatus === "healthy" ? "ready" : "fallback";

  return (
    <header className="clinical-topbar">
      <button className="mobile-menu-button" onClick={onMenuClick} aria-label="Mở menu">
        <Menu size={20} />
      </button>

      <div className="topbar-title">
        <span className="eyebrow">{page?.eyebrow || "Clinical workspace"}</span>
        <h1>{page?.title}</h1>
        <p>{page?.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <div className="quick-search">
          <Search size={16} />
          <span>Tìm nhanh trong dữ liệu y học</span>
        </div>
        <div className="status-row">
          <SystemStatusBadge type="backend" status={backendStatus} />
          <SystemStatusBadge type="database" status={databaseStatus} />
          <SystemStatusBadge type="ai" status={aiStatus} />
        </div>
        <div className="topbar-user">
          <UserRound size={16} />
          <span>{user?.fullName || user?.username || user?.email}</span>
        </div>
      </div>
    </header>
  );
}
