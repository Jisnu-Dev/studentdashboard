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

// ── Result analysis & remedial actions ─────────────────────────────────────────
export const analysis = {
  get: (batchId, examId, exam) =>
    request(`/batches/${batchId}/exams/${examId}/analysis?exam=${exam}`),

  pdfUrl: (batchId, examId, exam) =>
    `${API_BASE}/batches/${batchId}/exams/${examId}/analysis/pdf?exam=${exam}`,

  listRemedial: (batchId, examId) =>
    request(`/batches/${batchId}/exams/${examId}/remedial`),

  addRemedial: (batchId, examId, data) =>
    request(`/batches/${batchId}/exams/${examId}/remedial`, {
      method: "POST",
      body: JSON.stringify(data),
    }),

  deleteRemedial: (batchId, examId, actionId) =>
    request(`/batches/${batchId}/exams/${examId}/remedial/${actionId}`, { method: "DELETE" }),
};

// ── Documents (uploads) ────────────────────────────────────────────────────────
export const documents = {
  list: (batchId, category) =>
    request(`/batches/${batchId}/documents${category ? `?category=${category}` : ""}`),

  // fields: { category, title, notes?, from_date?, to_date? }
  upload: async (batchId, studentId, fields, file) => {
    const form = new FormData();
    Object.entries(fields).forEach(([k, v]) => { if (v) form.append(k, v); });
    form.append("file", file);
    const token = getToken();
    const res = await fetch(`${API_BASE}/batches/${batchId}/students/${studentId}/documents`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
      body: form,
    });
    const data = await res.json().catch(() => null);
    if (!res.ok) {
      const detail = data?.detail;
      throw new Error((Array.isArray(detail) ? detail[0]?.msg : detail) || `Upload failed (${res.status})`);
    }
    return data;
  },

  delete: (batchId, documentId) =>
    request(`/batches/${batchId}/documents/${documentId}`, { method: "DELETE" }),

  downloadUrl: (batchId, documentId) =>
    `${API_BASE}/batches/${batchId}/documents/${documentId}/download`,
};

// ── Mentor file ────────────────────────────────────────────────────────────────
function recordApi(resource) {
  return {
    list: (batchId) => request(`/batches/${batchId}/${resource}`),

    create: (batchId, data) =>
      request(`/batches/${batchId}/${resource}`, {
        method: "POST",
        body: JSON.stringify(data),
      }),

    delete: (batchId, recordId) =>
      request(`/batches/${batchId}/${resource}/${recordId}`, { method: "DELETE" }),
  };
}

export const mentorFile = {
  summary: (batchId) => request(`/batches/${batchId}/mentor-file/summary`),

  coverUrl: (batchId) => `${API_BASE}/batches/${batchId}/mentor-file/cover`,
};

export const communications = {
  ...recordApi("communications"),

  pdfUrl: (batchId) => `${API_BASE}/batches/${batchId}/communications/pdf`,
};

export const parentMeetings = {
  ...recordApi("parent-meetings"),

  pdfUrl: (batchId, meetingId) =>
    `${API_BASE}/batches/${batchId}/parent-meetings/${meetingId}/pdf`,
};

export const achievements = {
  ...recordApi("achievements"),

  pdfUrl: (batchId, studentId, academicYear) =>
    `${API_BASE}/batches/${batchId}/students/${studentId}/achievements/pdf?academic_year=${encodeURIComponent(academicYear)}`,
};

export const condonations = {
  ...recordApi("condonations"),

  pdfUrl: (batchId, condonationId) =>
    `${API_BASE}/batches/${batchId}/condonations/${condonationId}/pdf`,
};

export const semesterResults = {
  list: (batchId) => request(`/batches/${batchId}/semester-results`),

  save: (batchId, records) =>
    request(`/batches/${batchId}/semester-results`, {
      method: "PUT",
      body: JSON.stringify({ records }),
    }),

  pdfUrl: (batchId, academicYear) =>
    `${API_BASE}/batches/${batchId}/semester-results/pdf?academic_year=${encodeURIComponent(academicYear)}`,
};

// ── AI ─────────────────────────────────────────────────────────────────────────
export const ai = {
  // Computed metrics and risk level, plus the last saved report and study plan
  overview: (batchId, studentId) =>
    request(`/batches/${batchId}/students/${studentId}/ai/overview`),

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
