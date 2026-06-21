import { AlertCircle } from "lucide-react";
import clsx from "clsx";

export function Input({
  label,
  icon: Icon,
  error,
  className = "",
  textarea = false,
  ...props
}) {
  const Field = textarea ? "textarea" : "input";

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
        <Field
          className={clsx(
            "w-full border rounded-[var(--radius-md)] bg-white text-slate-900 placeholder:text-slate-400",
            "transition-all duration-200",
            "focus:outline-none focus:ring-2 focus:ring-teal-500/30 focus:border-teal-500",
            error
              ? "border-red-300 focus:ring-red-500/30 focus:border-red-500"
              : "border-slate-200 hover:border-slate-300",
            Icon ? "pl-10 pr-3" : "px-3",
            textarea ? "min-h-[110px] py-2.5 resize-y" : "h-11",
          )}
          {...props}
        />
      </div>
      {error && (
        <span className="flex items-center gap-1.5 text-xs font-medium text-red-500">
          <AlertCircle size={13} />
          {error}
        </span>
      )}
    </label>
  );
}
