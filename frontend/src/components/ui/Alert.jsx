import { AlertTriangle, CheckCircle2, Info, XCircle } from "lucide-react";
import clsx from "clsx";

const CONFIG = {
  info: {
    icon: Info,
    classes: "text-blue-800 bg-blue-50 border-blue-200/70",
  },
  success: {
    icon: CheckCircle2,
    classes: "text-emerald-800 bg-emerald-50 border-emerald-200/70",
  },
  warning: {
    icon: AlertTriangle,
    classes: "text-amber-800 bg-amber-50 border-amber-200/70",
  },
  danger: {
    icon: XCircle,
    classes: "text-red-800 bg-red-50 border-red-200/70",
  },
};

export function Alert({ children, tone = "info", className = "" }) {
  const { icon: Icon, classes } = CONFIG[tone] || CONFIG.info;

  return (
    <div
      className={clsx(
        "flex items-start gap-3 px-4 py-3 rounded-[var(--radius-md)] border text-sm leading-relaxed",
        classes,
        className
      )}
    >
      <Icon size={18} className="shrink-0 mt-0.5" />
      <div>{children}</div>
    </div>
  );
}
