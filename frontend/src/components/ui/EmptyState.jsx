import { ClipboardList } from "lucide-react";
import clsx from "clsx";
import { useGsapReveal } from "../../hooks/useGsapReveal";

export function EmptyState({ icon: Icon = ClipboardList, title, children, className = "" }) {
  const revealRef = useGsapReveal({
    selector: "self",
    y: 8,
    duration: 0.32,
    stagger: 0,
  });

  return (
    <div
      ref={revealRef}
      className={clsx(
        "flex flex-col items-center justify-center text-center py-12 px-6",
        className
      )}
    >
      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center mb-4">
        <Icon size={28} className="text-slate-400" />
      </div>
      <h3 className="text-base font-bold text-slate-700 m-0">{title}</h3>
      {children && (
        <p className="text-sm text-slate-500 mt-1.5 m-0 max-w-sm">{children}</p>
      )}
    </div>
  );
}
