export function hasValue(value) {
  return value !== null && value !== undefined && String(value).trim() !== "";
}

export function getItems(data) {
  if (Array.isArray(data)) return data;
  return data?.items ?? data?.data ?? [];
}

export function getTotal(data) {
  if (typeof data?.total === "number") return data.total;
  return getItems(data).length;
}

export function truncate(value, max = 160) {
  if (!hasValue(value)) return "";
  const text = String(value).trim();
  return text.length > max ? `${text.slice(0, max).trim()}...` : text;
}

export function fallback(value, empty = "-") {
  return hasValue(value) ? value : empty;
}

export function formatScore(value) {
  if (!hasValue(value)) return "-";
  return Number(value).toFixed(4);
}

export function formatPercent(value) {
  if (!hasValue(value)) return "-";
  return `${value}%`;
}

export function formatDateTime(value) {
  if (!hasValue(value)) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

export function pageCount(total, pageSize) {
  return Math.max(1, Math.ceil(Number(total || 0) / Number(pageSize || 1)));
}

export function normalizeApiError(message) {
  const text = String(message || "");
  if (text.includes("cơ sở dữ liệu") || text.includes("database")) {
    return "Backend chưa kết nối được cơ sở dữ liệu. Vui lòng kiểm tra SQL Server.";
  }
  if (text.includes("AI service") || text.includes("AI_MODEL")) {
    return "AI service chưa khả dụng. Hệ thống có thể dùng dữ liệu liên kết sẵn có để thay thế.";
  }
  if (text.includes("Failed to fetch") || text.includes("NetworkError")) {
    return "Không thể tải dữ liệu. Vui lòng kiểm tra Backend hoặc thử lại sau.";
  }
  return text || "Không thể tải dữ liệu. Vui lòng thử lại sau.";
}

export const FALLBACK_SOURCE_MESSAGE =
  "AI service hiện chưa khả dụng, hệ thống đang tạm dùng dữ liệu liên kết có sẵn trong cơ sở dữ liệu để gợi ý kết quả.";

export const DEFAULT_EXPLANATION_MESSAGE =
  "Liên kết được suy ra từ dữ liệu công dụng/chỉ định có sẵn của thuốc trong cơ sở dữ liệu.";

export const STANDARD_MEDICAL_WARNING =
  "Kết quả chỉ phục vụ học tập, nghiên cứu và tham khảo. Không dùng để tự chẩn đoán, kê đơn hoặc thay thế tư vấn của bác sĩ/dược sĩ.";

export function hasBrokenVietnameseEncoding(value) {
  const text = String(value || "");
  if (!text) return false;
  return (
    text.includes("�") ||
    /[A-Za-zÀ-ỹ]\?[A-Za-zÀ-ỹ]/.test(text) ||
    /(Liên k\?|công d\?|c\?a|thu\?c|b\?nh|tr\?c|ti\?p|d\? li\?u|ch\? đ\?nh)/i.test(text)
  );
}

export function sanitizeClinicalText(value, fallback = DEFAULT_EXPLANATION_MESSAGE) {
  const text = String(value || "").trim();
  if (!text || hasBrokenVietnameseEncoding(text)) return fallback;
  if (text.includes("Nguon diem: DATABASE_FALLBACK")) return FALLBACK_SOURCE_MESSAGE;
  if (text.includes("Nguon diem:")) return fallback;
  return text;
}
