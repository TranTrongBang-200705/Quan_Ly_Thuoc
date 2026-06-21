import { useState, useRef, useEffect } from "react";
import { ChevronDown, LogOut, Menu } from "lucide-react";
import clsx from "clsx";
import { SystemStatusBadge } from "../medical";
import { MobileDrawer } from "./MobileDrawer";
import { useGsapReveal } from "../../hooks/useGsapReveal";

export function TopNavigation({
  navItems,
  activePage,
  onNavigate,
  user,
  roles,
  onLogout,
  health,
}) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef(null);
  const navRevealRef = useGsapReveal({
    selector: "self",
    y: -12,
    duration: 0.36,
    stagger: 0,
  });

  const backendStatus = health?.status === "healthy" ? "online" : "offline";
  const databaseStatus = health?.status === "healthy" ? "healthy" : "unknown";
  const aiStatus = health?.aiStatus === "healthy" ? "ready" : "fallback";

  /* Flat list for top-level display */
  const allItems = navItems.flatMap((g) => g.items);

  /* Close user menu on outside click */
  useEffect(() => {
    function handleClick(e) {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  return (
    <>
      <header
        ref={navRevealRef}
        className={clsx(
          "fixed top-0 left-0 right-0 z-50",
          "bg-[rgba(246,251,255,0.88)] backdrop-blur-xl",
          "border-b border-[var(--color-border)]",
          "shadow-[var(--shadow-glass)]"
        )}
      >
        <div className="mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-8 py-3 lg:py-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex min-w-0 items-center gap-3">
              <button
                className="lg:hidden flex items-center justify-center w-10 h-10 rounded-[var(--radius-md)] hover:bg-white/80 transition-colors border border-transparent hover:border-slate-200"
                onClick={() => setMobileOpen(true)}
                aria-label="Mở menu"
              >
                <Menu size={22} className="text-slate-700" />
              </button>

              <button
                onClick={() => onNavigate("dashboard")}
                className="flex min-w-0 items-center gap-3 border-0 bg-transparent p-0 text-left"
              >
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-400 to-cyan-400 flex items-center justify-center text-white font-black text-sm shrink-0 shadow-sm">
                  DD
                </div>
                <div className="min-w-0">
                  <div className="text-[15px] sm:text-base font-extrabold text-slate-900 leading-tight truncate">
                    DrugDiseaseML
                  </div>
                  <div className="text-[10px] sm:text-[11px] font-bold text-teal-600 tracking-wide uppercase truncate">
                    AI Medical Intelligence
                  </div>
                </div>
              </button>
            </div>

            <div className="flex min-w-0 items-center justify-end gap-2 sm:gap-3">
              <div className="hidden md:flex items-center gap-2">
                <SystemStatusBadge type="backend" status={backendStatus} />
                <SystemStatusBadge type="database" status={databaseStatus} />
                <SystemStatusBadge type="ai" status={aiStatus} />
              </div>

              <div ref={userMenuRef} className="relative shrink-0">
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className={clsx(
                    "flex items-center gap-2 h-10 px-2.5 sm:px-3 rounded-[var(--radius-full)] border transition-all duration-200 shadow-sm",
                    userMenuOpen
                      ? "border-teal-200 bg-teal-50"
                      : "border-[var(--color-border)] bg-white/90 hover:bg-white"
                  )}
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-white text-xs font-bold">
                    {(user?.fullName || user?.email || "U")
                      .slice(0, 1)
                      .toUpperCase()}
                  </div>
                  <span className="hidden sm:inline text-sm font-semibold text-slate-700 max-w-[140px] truncate">
                    {user?.fullName || user?.username || "Người dùng"}
                  </span>
                  <ChevronDown
                    size={14}
                    className={clsx(
                      "text-slate-400 transition-transform duration-200",
                      userMenuOpen && "rotate-180"
                    )}
                  />
                </button>

                {userMenuOpen && (
                  <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-[var(--radius-lg)] border border-[var(--color-border)] shadow-[var(--shadow-card)] py-2 animate-[fade-in_0.15s_ease-out]">
                    <div className="px-4 py-3 border-b border-slate-100">
                      <p className="text-sm font-bold text-slate-900 m-0">
                        {user?.fullName || user?.username || "Người dùng"}
                      </p>
                      <p className="text-xs text-slate-500 mt-0.5 m-0">
                        {user?.email}
                      </p>
                      <p className="text-xs text-teal-600 font-semibold mt-1 m-0">
                        {roles.join(", ") || "USER"}
                      </p>
                    </div>

                    <div className="md:hidden px-4 py-2 border-b border-slate-100 flex flex-wrap gap-1.5">
                      <SystemStatusBadge type="backend" status={backendStatus} />
                      <SystemStatusBadge type="database" status={databaseStatus} />
                      <SystemStatusBadge type="ai" status={aiStatus} />
                    </div>

                    <button
                      onClick={() => {
                        setUserMenuOpen(false);
                        onLogout();
                      }}
                      className="w-full flex items-center gap-2.5 px-4 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-50 transition-colors border-0 bg-transparent text-left"
                    >
                      <LogOut size={16} />
                      Đăng xuất
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          <nav
            className="mt-3 hidden lg:flex items-center gap-1.5 overflow-x-auto rounded-[22px] border border-teal-200/70 bg-white/75 p-1.5 shadow-[0_12px_32px_rgba(15,23,42,0.06)]"
            aria-label="Điều hướng chính"
          >
            {allItems.map((item) => {
              const Icon = item.icon;
              const isActive = activePage === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onNavigate(item.id)}
                  className={clsx(
                    "flex shrink-0 items-center gap-2 whitespace-nowrap rounded-2xl border px-3.5 py-2 text-[13px] font-bold transition-all duration-200",
                    isActive
                      ? "border-teal-300 bg-gradient-to-r from-teal-50 to-cyan-50 text-teal-700 shadow-sm"
                      : "border-transparent bg-transparent text-slate-500 hover:border-slate-200 hover:bg-white hover:text-slate-900"
                  )}
                  aria-current={isActive ? "page" : undefined}
                >
                  <Icon size={16} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Mobile drawer */}
      <MobileDrawer
        open={mobileOpen}
        onClose={() => setMobileOpen(false)}
        navItems={navItems}
        activePage={activePage}
        onNavigate={(id) => {
          onNavigate(id);
          setMobileOpen(false);
        }}
        user={user}
        roles={roles}
        onLogout={() => {
          setMobileOpen(false);
          onLogout();
        }}
      />
    </>
  );
}
