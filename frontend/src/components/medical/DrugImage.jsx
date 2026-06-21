import { Pill } from "lucide-react";
import { useEffect, useState } from "react";
import { hasValue } from "../../utils/format";
import clsx from "clsx";

export function DrugImage({ src, alt, large = false, className = "" }) {
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    setFailed(false);
  }, [src]);

  const sizeClass = large ? "aspect-[4/3] min-h-[220px]" : "aspect-[16/9]";

  if (!hasValue(src) || failed) {
    return (
      <div
        className={clsx(
          "w-full overflow-hidden rounded-[var(--radius-md)] border border-slate-200 bg-gradient-to-br from-slate-50 to-cyan-50 flex flex-col items-center justify-center gap-1.5 text-teal-600",
          sizeClass,
          className
        )}
      >
        <Pill size={large ? 36 : 24} />
        <span className="text-xs font-semibold text-teal-500">Không có ảnh</span>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        "w-full overflow-hidden rounded-[var(--radius-md)] border border-slate-200 bg-gradient-to-br from-slate-50 to-cyan-50 flex items-center justify-center",
        sizeClass,
        className
      )}
    >
      <img
        className="h-full w-full object-contain p-2"
        src={src}
        alt={alt || "Ảnh thuốc"}
        loading="lazy"
        onError={() => setFailed(true)}
      />
    </div>
  );
}
