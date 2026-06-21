import clsx from "clsx";

export function Select({ label, icon: Icon, children, className = "", ...props }) {
  return (
    <label className={clsx("flex flex-col gap-1.5", className)}>
      {label && (
        <span className="text-sm font-semibold text-slate-700">{label}</span>
      )}
      <div className="relative">
        {Icon && (
          <Icon
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
          />
        )}
        <select
          className={clsx(
            "w-full h-11 border border-slate-200 rounded-[var(--radius-md)] bg-white text-slate-900",
            "transition-all duration-200 appearance-none",
            "focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500",
            "hover:border-slate-300",
            Icon ? "pl-10 pr-8" : "px-3 pr-8"
          )}
          {...props}
        >
          {children}
        </select>
        {/* Custom dropdown arrow */}
        <svg
          className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </div>
    </label>
  );
}
