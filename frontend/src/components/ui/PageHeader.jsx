import clsx from "clsx";
import { useGsapReveal } from "../../hooks/useGsapReveal";

export function PageHeader({ eyebrow, title, subtitle, actions, className = "" }) {
  const revealRef = useGsapReveal({
    selector: "self",
    y: 14,
    duration: 0.38,
    dependencies: [title],
  });

  return (
    <header
      ref={revealRef}
      className={clsx("flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-6", className)}
    >
      <div>
        {eyebrow && (
          <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
            {eyebrow}
          </span>
        )}
        <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 m-0 leading-tight">
          {title}
        </h1>
        {subtitle && (
          <p className="text-sm text-slate-500 mt-1.5 m-0 max-w-2xl leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
    </header>
  );
}
