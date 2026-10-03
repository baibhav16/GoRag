export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

/* ✅ Upload PDF */
export async function uploadPDF(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error("Upload failed")  ;
  }

  return res.json();
}

/* ✅ Ask Question */
export async function askQuestion(query: string, doc_id: string) {
  const res = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      doc_id,
    }),
  });

  if (!res.ok) {
    throw new Error("Ask failed");
  }

  return res.json();
}
