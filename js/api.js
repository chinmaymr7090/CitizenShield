// CitizenShield - Backend API Client & Session Vault

const API_BASE = window.location.origin.includes(":5000")
  ? ""
  : "http://127.0.0.1:5000";

let cachedUser = null;

export function getToken() {
  return localStorage.getItem("cs_auth_token");
}

export function setToken(token) {
  if (token) {
    localStorage.setItem("cs_auth_token", token);
  } else {
    localStorage.removeItem("cs_auth_token");
  }
}

export function getCurrentUser() {
  const userJson = localStorage.getItem("cs_auth_user");
  if (!userJson) return null;
  try {
    return JSON.parse(userJson);
  } catch (e) {
    return null;
  }
}

export function setCurrentUser(user) {
  if (user) {
    cachedUser = user;
    localStorage.setItem("cs_auth_user", JSON.stringify(user));
  } else {
    cachedUser = null;
    localStorage.removeItem("cs_auth_user");
  }
}

async function request(endpoint, options = {}) {
  const token = getToken();
  const headers = options.headers ? { ...options.headers } : {};

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = "Bearer " + token;
  }

  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  options.headers = headers;

  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, options);
    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      const err = new Error(data.error || `Server returned error (${res.status})`);
      err.status = res.status;
      err.data = data;
      throw err;
    }

    return data;
  } catch (err) {
    if (err.name === "TypeError" && err.message.includes("Failed to fetch")) {
      throw new Error("Unable to connect to CitizenShield backend server. Please verify the Python server is running (`python run.py`).");
    }
    throw err;
  }
}

// Auth API
export async function apiLogin(email, password) {
  const data = await request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password })
  });
  setToken(data.token);
  setCurrentUser(data.user);
  return data;
}

export async function apiRegister(name, email, password, phone = "") {
  const data = await request("/api/auth/register", {
    method: "POST",
    body: JSON.stringify({ name, email, password, phone })
  });
  return data;
}

export async function apiGetProfile() {
  const data = await request("/api/auth/me");
  setCurrentUser(data.user);
  return data.user;
}

export async function apiLogout() {
  try {
    await request("/api/auth/logout", { method: "POST" });
  } finally {
    setToken(null);
    setCurrentUser(null);
  }
}

// Real AI Vision Detection API
export async function apiAnalyzeImage(imageFile) {
  const formData = new FormData();
  formData.append("image", imageFile);
  return await request("/api/ai/analyze-image", {
    method: "POST",
    body: formData
  });
}

// Duplicate Detection Check API
export async function apiCheckDuplicate(category, latitude, longitude) {
  return await request("/api/reports/check-duplicate", {
    method: "POST",
    body: JSON.stringify({ category, latitude, longitude })
  });
}

// Live Colour-Coded Zone Monitoring API
export async function apiGetZonesSummary() {
  return await request("/api/zones");
}

export async function apiGetZoneComplaints(zoneId) {
  return await request(`/api/zones/${encodeURIComponent(zoneId)}/complaints`);
}

// AI Dashboard Metrics API
export async function apiGetAiMetrics() {
  return await request("/api/ai/metrics");
}

// Reports API
export async function apiSubmitReport(formData) {
  return await request("/api/reports", {
    method: "POST",
    body: formData
  });
}

export async function apiGetMyReports() {
  const data = await request("/api/reports/my");
  return data.reports || [];
}

export async function apiTrackReport(reportId) {
  const data = await request(`/api/reports/track/${encodeURIComponent(reportId)}`);
  return data.report;
}

export async function apiGetAllReports(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== "ALL") params.append("status", filters.status);
  if (filters.category && filters.category !== "ALL") params.append("category", filters.category);
  if (filters.priority && filters.priority !== "ALL") params.append("priority", filters.priority);
  if (filters.search) params.append("search", filters.search);

  const query = params.toString() ? `?${params.toString()}` : "";
  const data = await request(`/api/reports/all${query}`);
  return data.reports || [];
}

export async function apiGetMapPins() {
  const data = await request("/api/reports/map");
  return data.pins || [];
}

export async function apiUpdateReportStatus(reportId, newStatus, remarks, department = "", afterImageFile = null, priority = "") {
  let body;
  if (afterImageFile) {
    const fd = new FormData();
    fd.append("status", newStatus);
    fd.append("remarks", remarks);
    if (department) fd.append("department", department);
    if (priority) fd.append("priority", priority);
    fd.append("after_image", afterImageFile);
    body = fd;
  } else {
    body = JSON.stringify({
      status: newStatus,
      remarks,
      department,
      priority
    });
  }

  return await request(`/api/reports/${encodeURIComponent(reportId)}/status`, {
    method: "PATCH",
    body: body
  });
}

export async function apiGetAdminMetrics() {
  return await request("/api/admin/metrics");
}
