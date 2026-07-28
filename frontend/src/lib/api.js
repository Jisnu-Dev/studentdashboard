const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

function getToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 204) return null;

  const data = await res.json().catch(() => null);

  if (!res.ok) {
    const message =
      data?.detail ||
      (Array.isArray(data?.detail) ? data.detail[0]?.msg : null) ||
      `Request failed (${res.status})`;
    throw new Error(message);
  }

  return data;
}

// ── Auth ───────────────────────────────────────────────────────────────────────
export const auth = {
  register: (name, email, password) =>
    request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    }),

  login: async (email, password) => {
    const form = new URLSearchParams({ username: email, password });
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) throw new Error(data?.detail || "Login failed");
    return data;
  },

  me: () => request("/auth/me"),
};

// ── Batches ────────────────────────────────────────────────────────────────────
export const batches = {
  list: () => request("/batches/"),

  get: (id) => request(`/batches/${id}`),

  create: (department, batch_year) =>
    request("/batches/", {
      method: "POST",
      body: JSON.stringify({ department, batch_year }),
    }),

  update: (id, data) =>
    request(`/batches/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id) => request(`/batches/${id}`, { method: "DELETE" }),

  exportPdf: (id) => `${API_BASE}/batches/${id}/export/pdf`,
};

// ── Students ───────────────────────────────────────────────────────────────────
export const students = {
  list: (batchId) => request(`/batches/${batchId}/students`),

  add: (batchId, register_number, name) =>
    request(`/batches/${batchId}/students`, {
      method: "POST",
      body: JSON.stringify({ register_number, name }),
    }),

  update: (batchId, studentId, data) =>
    request(`/batches/${batchId}/students/${studentId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (batchId, studentId) =>
    request(`/batches/${batchId}/students/${studentId}`, { method: "DELETE" }),
};

// ── Counseling ─────────────────────────────────────────────────────────────────
export const counseling = {
  list: (batchId, studentId) =>
    request(`/batches/${batchId}/students/${studentId}/counseling`),

  get: (batchId, studentId, sessionId) =>
    request(`/batches/${batchId}/students/${studentId}/counseling/${sessionId}`),

  create: (batchId, studentId, data) =>
    request(`/batches/${batchId}/students/${studentId}/counseling`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  delete: (batchId, studentId, sessionId) =>
    request(`/batches/${batchId}/students/${studentId}/counseling/${sessionId}`, {
      method: "DELETE",
    }),

  pdfUrl: (batchId, studentId, sessionId) =>
    `${API_BASE}/batches/${batchId}/students/${studentId}/counseling/${sessionId}/pdf`,
};

// ── Meetings ───────────────────────────────────────────────────────────────────
export const meetings = {
  list: (batchId) => request(`/batches/${batchId}/meetings`),

  get: (batchId, meetingId) => request(`/batches/${batchId}/meetings/${meetingId}`),

  create: (batchId, data) =>
    request(`/batches/${batchId}/meetings`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (batchId, meetingId, data) =>
    request(`/batches/${batchId}/meetings/${meetingId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (batchId, meetingId) =>
    request(`/batches/${batchId}/meetings/${meetingId}`, { method: "DELETE" }),

  circularUrl: (batchId, meetingId) =>
    `${API_BASE}/batches/${batchId}/meetings/${meetingId}/circular`,

  minutesUrl: (batchId, meetingId) =>
    `${API_BASE}/batches/${batchId}/meetings/${meetingId}/minutes`,

  // Attendance
  getAttendance: (batchId, meetingId) =>
    request(`/batches/${batchId}/meetings/${meetingId}/attendance`),

  saveAttendance: (batchId, meetingId, records) =>
    request(`/batches/${batchId}/meetings/${meetingId}/attendance`, {
      method: "PUT",
      body: JSON.stringify({ records }),
    }),
};

// ── Exams ──────────────────────────────────────────────────────────────────────
export const exams = {
  list: (batchId) => request(`/batches/${batchId}/exams`),

  get: (batchId, examId) => request(`/batches/${batchId}/exams/${examId}`),

  create: (batchId, data) =>
    request(`/batches/${batchId}/exams`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  update: (batchId, examId, data) =>
    request(`/batches/${batchId}/exams/${examId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  delete: (batchId, examId) =>
    request(`/batches/${batchId}/exams/${examId}`, { method: "DELETE" }),

  getMarks: (batchId, examId) =>
    request(`/batches/${batchId}/exams/${examId}/marks`),

  saveMarks: (batchId, examId, records) =>
    request(`/batches/${batchId}/exams/${examId}/marks`, {
      method: "PUT",
      body: JSON.stringify({ records }),
    }),

  pt1PdfUrl: (batchId, examId) =>
    `${API_BASE}/batches/${batchId}/exams/${examId}/pdf/pt1`,

  pt2PdfUrl: (batchId, examId) =>
    `${API_BASE}/batches/${batchId}/exams/${examId}/pdf/pt2`,

  semesterPdfUrl: (batchId, examId) =>
    `${API_BASE}/batches/${batchId}/exams/${examId}/pdf/semester`,
};

// ── AI ─────────────────────────────────────────────────────────────────────────
export const ai = {
  report: (batchId, studentId) =>
    request(`/batches/${batchId}/students/${studentId}/ai/report`, { method: "POST" }),

  schedule: (batchId, studentId) =>
    request(`/batches/${batchId}/students/${studentId}/ai/schedule`, { method: "POST" }),

  chat: (batchId, studentId, message, history = []) =>
    request(`/batches/${batchId}/students/${studentId}/ai/chat`, {
      method: "POST",
      body: JSON.stringify({ message, history }),
    }),
};
