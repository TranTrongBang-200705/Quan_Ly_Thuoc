import { TopNavigation } from "./TopNavigation";
import { PageHeader } from "../ui";
import { useGsapReveal } from "../../hooks/useGsapReveal";

export function AppLayout({
  navItems,
  activePage,
  pageMeta,
  onNavigate,
  user,
  roles,
  onLogout,
  health,
  children,
}) {
  const contentRevealRef = useGsapReveal({
    selector: "children",
    y: 16,
    duration: 0.36,
    stagger: 0.04,
    dependencies: [pageMeta?.title],
  });

  return (
    <div className="min-h-screen">
      <TopNavigation
        navItems={navItems}
        activePage={activePage}
        onNavigate={onNavigate}
        user={user}
        roles={roles}
        onLogout={onLogout}
        health={health}
      />

      {/* Main content with top offset for fixed nav */}
      <main className="pt-[76px] lg:pt-[132px]">
        <div className="w-full max-w-[1380px] mx-auto px-4 sm:px-6 lg:px-9 py-6 lg:py-8">
          {/* Page header from meta */}
          {pageMeta && (
            <PageHeader
              eyebrow={pageMeta.eyebrow}
              title={pageMeta.title}
              subtitle={pageMeta.subtitle}
            />
          )}
          <div ref={contentRevealRef}>
            {children}
          </div>
        </div>
      </main>
    </div>
  );
}
