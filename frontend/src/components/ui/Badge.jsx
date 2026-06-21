import clsx from "clsx";

const TONES = {
  emerald: "text-emerald-700 bg-emerald-50 border-emerald-200/60",
  cyan: "text-cyan-700 bg-cyan-50 border-cyan-200/60",
  teal: "text-teal-700 bg-teal-50 border-teal-200/60",
  blue: "text-blue-700 bg-blue-50 border-blue-200/60",
  amber: "text-amber-700 bg-amber-50 border-amber-200/60",
  red: "text-red-700 bg-red-50 border-red-200/60",
  slate: "text-slate-600 bg-slate-100 border-slate-200/60",
};

export function Badge({ children, tone = "slate", className = "", dot = false }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 h-6 px-2.5 rounded-full text-xs font-bold border whitespace-nowrap",
        TONES[tone] || TONES.slate,
        className
      )}
    >
      {dot && (
        <span
          className={clsx(
            "w-1.5 h-1.5 rounded-full shrink-0",
            tone === "emerald" || tone === "teal" || tone === "cyan"
              ? "bg-current animate-[pulse-dot_2s_ease-in-out_infinite]"
              : "bg-current"
          )}
        />
      )}
      {children}
    </span>
  );
}
