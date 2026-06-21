import { Loader2 } from "lucide-react";
import clsx from "clsx";

const VARIANTS = {
  primary:
    "text-white bg-gradient-to-r from-teal-600 to-cyan-600 hover:from-teal-500 hover:to-cyan-500 shadow-sm hover:shadow-md hover:-translate-y-0.5 active:translate-y-0",
  secondary:
    "text-slate-700 bg-white border border-[var(--color-border-strong)] hover:bg-slate-50 hover:border-slate-300 shadow-sm",
  ghost:
    "text-slate-600 bg-transparent hover:bg-slate-100 border border-transparent",
  danger:
    "text-white bg-gradient-to-r from-red-500 to-red-600 hover:from-red-400 hover:to-red-500 shadow-sm hover:shadow-md",
};

const SIZES = {
  sm: "h-8 px-3 text-xs gap-1.5 rounded-lg",
  md: "h-10 px-4 text-sm gap-2 rounded-[var(--radius-md)]",
  lg: "h-12 px-6 text-base gap-2.5 rounded-[var(--radius-md)]",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  className = "",
  loading = false,
  disabled = false,
  ...props
}) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center font-bold transition-all duration-200 whitespace-nowrap",
        VARIANTS[variant] || VARIANTS.primary,
        SIZES[size] || SIZES.md,
        (disabled || loading) && "opacity-55 cursor-not-allowed pointer-events-none",
        className
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 size={16} className="animate-spin" />}
      {children}
    </button>
  );
}
