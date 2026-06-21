import { LogOut, X } from "lucide-react";
import clsx from "clsx";

export function MobileDrawer({
  open,
  onClose,
  navItems,
  activePage,
  onNavigate,
  user,
  roles,
  onLogout,
}) {
  return (
    <>
      {/* Backdrop */}
      <div
        className={clsx(
          "fixed inset-0 z-[60] bg-slate-900/40 backdrop-blur-sm transition-opacity duration-300",
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={onClose}
      />

      {/* Drawer panel */}
      <aside
        className={clsx(
          "fixed top-0 left-0 z-[61] w-[min(85vw,320px)] h-full",
          "bg-white shadow-2xl",
          "flex flex-col",
          "transition-transform duration-300 ease-out",
          open ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white font-black text-sm">
              DD
            </div>
            <div>
              <div className="text-sm font-extrabold text-slate-900">DrugDiseaseML</div>
              <div className="text-[10px] font-semibold text-teal-600 uppercase tracking-wide">
                AI Medical Intelligence
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-9 h-9 flex items-center justify-center rounded-lg hover:bg-slate-100 transition-colors border-0 bg-transparent"
            aria-label="Đóng menu"
          >
            <X size={20} className="text-slate-500" />
          </button>
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-3">
          {navItems.map((group) => (
            <div key={group.label} className="mb-4">
              <span className="block px-3 mb-2 text-[11px] font-bold text-teal-600 uppercase tracking-wider">
                {group.label}
              </span>
              {group.items.map((item) => {
                const Icon = item.icon;
                const isActive = activePage === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onNavigate(item.id)}
                    className={clsx(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-semibold transition-all duration-200 border-0 text-left mb-0.5",
                      isActive
                        ? "bg-gradient-to-r from-teal-50 to-cyan-50 text-teal-700"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-800 bg-transparent"
                    )}
                  >
                    <Icon size={18} />
                    {item.label}
                  </button>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Profile */}
        <div className="p-4 border-t border-slate-100">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white text-sm font-bold shrink-0">
              {(user?.fullName || user?.email || "U").slice(0, 1).toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold text-slate-900 truncate m-0">
                {user?.fullName || user?.username || "Người dùng"}
              </p>
              <p className="text-xs text-slate-500 truncate m-0">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={onLogout}
            className="w-full flex items-center justify-center gap-2 h-10 rounded-xl bg-red-50 text-red-600 text-sm font-semibold hover:bg-red-100 transition-colors border-0"
          >
            <LogOut size={16} />
            Đăng xuất
          </button>
        </div>
      </aside>
    </>
  );
}
