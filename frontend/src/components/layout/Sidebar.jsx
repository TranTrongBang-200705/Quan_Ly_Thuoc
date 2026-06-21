import { LogOut, X } from "lucide-react";
import { Button } from "../ui";

export function Sidebar({
  navItems,
  activePage,
  onNavigate,
  user,
  roles,
  onLogout,
  open,
  onClose,
}) {
  return (
    <>
      <div className={open ? "sidebar-backdrop show" : "sidebar-backdrop"} onClick={onClose} />
      <aside className={open ? "clinical-sidebar open" : "clinical-sidebar"}>
        <div className="sidebar-brand">
          <span className="brand-symbol">DD</span>
          <div>
            <strong>DrugDiseaseML</strong>
            <small>AI Medical Intelligence</small>
          </div>
          <button className="sidebar-close" onClick={onClose} aria-label="Đóng menu">
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {navItems.map((group) => (
            <div className="nav-group" key={group.label}>
              <span>{group.label}</span>
              {group.items.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    className={activePage === item.id ? "nav-link active" : "nav-link"}
                    onClick={() => {
                      onNavigate(item.id);
                      onClose();
                    }}
                  >
                    <Icon size={18} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        <div className="sidebar-profile">
          <div className="avatar">{(user?.fullName || user?.email || "U").slice(0, 1).toUpperCase()}</div>
          <div>
            <strong>{user?.fullName || user?.username || "Người dùng"}</strong>
            <small>{user?.email}</small>
            <small>{roles.join(", ") || "USER"}</small>
          </div>
          <Button variant="ghost" size="sm" onClick={onLogout}>
            <LogOut size={16} />
            Đăng xuất
          </Button>
        </div>
      </aside>
    </>
  );
}
