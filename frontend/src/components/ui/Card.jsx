import clsx from "clsx";

export function Card({ children, className = "", interactive = false, as: Tag = "section", ...props }) {
  return (
    <Tag
      className={clsx(
        "bg-white/95 border border-[var(--color-border)] rounded-[var(--radius-lg)] shadow-[var(--shadow-card)] p-5",
        interactive && "transition-shadow duration-200 hover:shadow-[var(--shadow-card-hover)] cursor-pointer",
        className
      )}
      {...props}
    >
      {children}
    </Tag>
  );
}
