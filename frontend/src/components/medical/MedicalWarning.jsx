import { ShieldAlert } from "lucide-react";
import clsx from "clsx";

export const MEDICAL_WARNING =
  "Kết quả chỉ phục vụ học tập, nghiên cứu và tham khảo, không thay thế tư vấn của bác sĩ hoặc dược sĩ.";

export function MedicalWarning({ compact = false, className = "" }) {
  return (
    <div
      className={clsx(
        "flex items-start gap-3 rounded-[var(--radius-lg)] border border-emerald-200/70 bg-emerald-50/60 text-emerald-800 leading-relaxed",
        compact ? "p-3 text-xs" : "p-4 text-sm",
        className
      )}
    >
      <ShieldAlert size={compact ? 18 : 22} className="shrink-0 text-emerald-600 mt-0.5" />
      <p className="m-0">{MEDICAL_WARNING}</p>
    </div>
  );
}
