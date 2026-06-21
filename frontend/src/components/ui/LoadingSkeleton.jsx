import clsx from "clsx";

export function LoadingSkeleton({ count = 6, variant = "card" }) {
  const isRow = variant === "row";
  return (
    <div
      className={clsx(
        "grid gap-4",
        isRow ? "grid-cols-1" : "grid-cols-1 sm:grid-cols-2 lg:grid-cols-3"
      )}
    >
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          className="bg-white/90 border border-[var(--color-border)] rounded-[var(--radius-lg)] p-5 space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]" />
          <div className="w-3/4 h-4 rounded-full bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]" />
          <div className="w-full h-3 rounded-full bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]" />
          <div className="w-1/2 h-3 rounded-full bg-gradient-to-r from-slate-100 via-slate-50 to-slate-100 bg-[length:200%_100%] animate-[shimmer_1.5s_ease-in-out_infinite]" />
        </div>
      ))}
    </div>
  );
}
