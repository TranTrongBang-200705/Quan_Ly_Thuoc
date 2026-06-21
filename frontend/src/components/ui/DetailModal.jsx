import { X } from "lucide-react";
import { useEffect } from "react";
import { createPortal } from "react-dom";
import { useGsapReveal } from "../../hooks/useGsapReveal";

/**
 * Generic detail modal rendered in a portal.
 * Usage:
 *   <DetailModal open={!!item} onClose={() => setItem(null)} title="...">
 *     {content}
 *   </DetailModal>
 */
export function DetailModal({ open, onClose, title, eyebrow, children }) {
  const modalRef = useGsapReveal({
    selector: "self",
    y: 18,
    duration: 0.28,
    dependencies: [open],
  });

  /* Close on Escape key */
  useEffect(() => {
    if (!open) return;
    function handleKey(e) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  /* Prevent body scroll when open */
  useEffect(() => {
    if (open) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => { document.body.style.overflow = ""; };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="detail-modal-backdrop"
      role="dialog"
      aria-modal="true"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div ref={modalRef} className="detail-modal">
        {/* Header */}
        <div className="detail-modal-header">
          <div className="min-w-0">
            {eyebrow && (
              <span className="inline-block text-xs font-bold text-teal-600 tracking-widest uppercase mb-1">
                {eyebrow}
              </span>
            )}
            <h2 className="text-base font-bold text-slate-900 m-0 leading-snug">
              {title}
            </h2>
          </div>
          <button
            type="button"
            className="detail-modal-close"
            onClick={onClose}
            aria-label="Đóng"
          >
            <X size={16} />
          </button>
        </div>

        {/* Body */}
        <div className="detail-modal-body">
          {children}
        </div>
      </div>
    </div>,
    document.body
  );
}
