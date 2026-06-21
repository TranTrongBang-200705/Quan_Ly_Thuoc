import { useEffect, useMemo, useState } from "react";
import clsx from "clsx";
import gsap from "gsap";
import { Card } from "../ui";
import { useReducedMotion } from "../../hooks/useReducedMotion";

const TONE_STYLES = {
  teal: {
    icon: "bg-teal-50 text-teal-600",
    value: "text-teal-700",
  },
  cyan: {
    icon: "bg-cyan-50 text-cyan-600",
    value: "text-cyan-700",
  },
  emerald: {
    icon: "bg-emerald-50 text-emerald-600",
    value: "text-emerald-700",
  },
  blue: {
    icon: "bg-blue-50 text-blue-600",
    value: "text-blue-700",
  },
};

export function StatCard({ icon: Icon, label, value, hint, tone = "teal" }) {
  const style = TONE_STYLES[tone] || TONE_STYLES.teal;
  const reducedMotion = useReducedMotion();
  const numericValue = useMemo(() => Number(value), [value]);
  const canCount = Number.isFinite(numericValue);
  const [displayValue, setDisplayValue] = useState(canCount ? 0 : value);

  useEffect(() => {
    if (!canCount || reducedMotion) {
      setDisplayValue(value ?? "—");
      return undefined;
    }

    const counter = { value: 0 };
    const tween = gsap.to(counter, {
      value: numericValue,
      duration: 0.72,
      ease: "power2.out",
      onUpdate: () => setDisplayValue(Math.round(counter.value).toLocaleString("vi-VN")),
      onComplete: () => setDisplayValue(numericValue.toLocaleString("vi-VN")),
    });

    return () => tween.kill();
  }, [canCount, numericValue, reducedMotion, value]);

  return (
    <Card className="!p-5">
      <div className="flex items-start gap-4">
        <div
          className={clsx(
            "w-11 h-11 rounded-[var(--radius-md)] flex items-center justify-center shrink-0",
            style.icon
          )}
        >
          {Icon && <Icon size={22} />}
        </div>
        <div className="min-w-0">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {label}
          </span>
          <strong className={clsx("block text-3xl font-black mt-0.5 leading-none", style.value)}>
            {displayValue ?? "—"}
          </strong>
          {hint && (
            <small className="block text-xs text-slate-400 mt-1.5">{hint}</small>
          )}
        </div>
      </div>
    </Card>
  );
}
