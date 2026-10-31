import { getToken } from "@/lib/auth";

const EXTENSIONS = {
  "application/pdf": ".pdf",
  "image/jpeg": ".jpg",
  "image/png": ".png",
  "image/webp": ".webp",
};

// Fetch a protected file with the bearer token and save it under `filename`.
// A filename without an extension gets one from the response's content type.
export async function downloadFile(url, filename) {
  const res = await fetch(url, { headers: { Authorization: `Bearer ${getToken()}` } });
  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new Error(data?.detail || "Download failed");
  }
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  const name = /\.\w{2,5}$/.test(filename) ? filename : filename + (EXTENSIONS[blob.type] || "");
  a.download = name.replace(/ /g, "_");
  a.click();
  URL.revokeObjectURL(a.href);
}
