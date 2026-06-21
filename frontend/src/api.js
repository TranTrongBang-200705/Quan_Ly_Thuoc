const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

const AUTH_STORAGE_KEY = "drug_disease_auth";

export function getStoredAuth() {
  try {
    const raw = localStorage.getItem(AUTH_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function saveStoredAuth(auth) {
  localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(auth));
}

export function clearStoredAuth() {
  localStorage.removeItem(AUTH_STORAGE_KEY);
}

function getAccessToken() {
  return getStoredAuth()?.accessToken || "";
}

async function request(path, options = {}) {
  const { auth = true, ...fetchOptions } = options;
  const token = auth ? getAccessToken() : "";

  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(fetchOptions.headers || {}),
    },
    ...fetchOptions,
  });

  if (response.status === 401) {
    const message = await readErrorMessage(
      response,
      "Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.",
    );
    clearStoredAuth();
    throw new Error(friendlyError(message));
  }

  if (response.status === 403) {
    throw new Error(
      await readErrorMessage(
        response,
        "Bạn không có quyền thực hiện thao tác này.",
      ),
    );
  }

  if (!response.ok) {
    throw new Error(
      friendlyError(await readErrorMessage(response, `Request failed with status ${response.status}`)),
    );
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

async function readErrorMessage(response, fallback) {
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    try {
      const errorBody = await response.json();
      return errorBody.detail || errorBody.message || errorBody.title || fallback;
    } catch {
      return fallback;
    }
  }

  const text = await response.text();
  return text || fallback;
}

function friendlyError(message) {
  const text = String(message || "");
  const lower = text.toLowerCase();

  if (lower.includes("database") || text.includes("cơ sở dữ liệu")) {
    return "Backend chưa kết nối được cơ sở dữ liệu. Vui lòng kiểm tra SQL Server.";
  }

  if (text.includes("AI service")) {
    return "AI service chưa khả dụng. Hệ thống có thể dùng dữ liệu liên kết sẵn có để thay thế.";
  }

  if (text.includes("Failed to fetch") || text.includes("NetworkError")) {
    return "Không thể tải dữ liệu. Vui lòng kiểm tra Backend hoặc thử lại sau.";
  }

  return text || "Không thể tải dữ liệu. Vui lòng kiểm tra Backend hoặc thử lại sau.";
}

function toQuery(params) {
  const query = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });

  const value = query.toString();
  return value ? `?${value}` : "";
}

function mapCatalogParams(params = {}) {
  return {
    tuKhoa: params.tuKhoa ?? params.keyword,
    page: params.page ?? 1,
    pageSize: params.pageSize ?? params.take ?? 12,
    sapXep: params.sapXep,
    nhaSanXuat: params.nhaSanXuat,
    nhomThuocId: params.nhomThuocId,
  };
}

function mapLinkParams(params = {}) {
  return {
    thuocId: params.thuocId ?? params.drugId,
    benhId: params.benhId ?? params.diseaseId,
  };
}

export const api = {
  getHealth() {
    return request("/health", { auth: false });
  },

  getModelInfo() {
    return request("/model/info");
  },

  register(payload) {
    return request("/auth/register", {
      auth: false,
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  login(payload) {
    return request("/auth/login", {
      auth: false,
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  me() {
    return request("/auth/me");
  },

  checkAdminAccess() {
    return request("/admin/access-check");
  },

  getDrugs(params = {}) {
    return request(`/thuoc${toQuery(mapCatalogParams(params))}`);
  },

  getDiseases(params = {}) {
    return request(`/benh${toQuery(mapCatalogParams(params))}`);
  },

  getDrug(id) {
    return request(`/thuoc/${id}`);
  },

  getDisease(id) {
    return request(`/benh/${id}`);
  },

  getLinks(params = {}) {
    return request(`/lien-ket-thuoc-benh${toQuery(mapLinkParams(params))}`);
  },

  getLinksByDrug(thuocId) {
    return request(`/lien-ket-thuoc-benh/theo-thuoc/${thuocId}`);
  },

  getLinksByDisease(benhId) {
    return request(`/lien-ket-thuoc-benh/theo-benh/${benhId}`);
  },

  getLookups() {
    return request("/lookups");
  },

  createPrediction(payload) {
    return request("/du-doan", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  getPredictionHistory() {
    return request("/du-doan/lich-su");
  },

  getPrediction(id) {
    return request(`/du-doan/${id}`);
  },

  getAdminPredictionHistory(params = {}) {
    return request(`/du-doan/admin/lich-su${toQuery(params)}`);
  },

  getAdminLinks(params = {}) {
    return request(`/admin/links${toQuery(mapLinkParams(params))}`);
  },

  createAdminLink(payload) {
    return request("/admin/links", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },

  updateAdminLink(linkId, payload) {
    return request(`/admin/links/${linkId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
  },

  deleteAdminLink(linkId) {
    return request(`/admin/links/${linkId}`, {
      method: "DELETE",
    });
  },

  createFeedback(payload) {
    return request("/phan-hoi-ket-qua", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
