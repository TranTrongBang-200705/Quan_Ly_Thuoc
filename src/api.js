const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "https://localhost:7001/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with status ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
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

export const api = {
  getDrugs(params = {}) {
    return request(`/drugs${toQuery(params)}`);
  },
  getDiseases(params = {}) {
    return request(`/diseases${toQuery(params)}`);
  },
  getLinks(params = {}) {
    return request(`/links${toQuery(params)}`);
  },
  getLookups() {
    return request("/lookups");
  },
  createPrediction(payload) {
    return request("/predictions", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
  getPredictionHistory(userId) {
    return request(`/predictions/history${toQuery({ userId })}`);
  },
  createFeedback(payload) {
    return request("/feedbacks", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  },
};
