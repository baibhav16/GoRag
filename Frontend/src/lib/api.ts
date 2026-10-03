export const API_BASE_URL = (
  import.meta.env.VITE_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

// Check if running on production (e.g., Vercel) with localhost API
if (
  typeof window !== "undefined" &&
  window.location.hostname !== "localhost" &&
  window.location.hostname !== "127.0.0.1" &&
  API_BASE_URL.includes("127.0.0.1")
) {
  console.warn(
    "⚠️ Warning: GoRag frontend is running on a production URL, but VITE_API_URL is pointing to localhost. " +
    "Please configure VITE_API_URL in your Vercel project environment variables to point to your Render backend URL."
  );
}

async function extractErrorMessage(res: Response, defaultMessage: string): Promise<string> {
  try {
    const data = await res.json();
    if (data && data.detail) {
      return typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
    }
    if (data && data.message) {
      return data.message;
    }
  } catch {
    try {
      const text = await res.text();
      if (text && text.trim().length > 0) {
        return text;
      }
    } catch {
      // Fallback
    }
  }
  return `${defaultMessage} (HTTP ${res.status})`;
}

/* ✅ Upload PDF */
export async function uploadPDF(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    });
  } catch (err: any) {
    throw new Error(
      `Cannot connect to backend (${API_BASE_URL}). If hosted on Render Free Tier, the backend may be waking up (takes ~60s) or check your CORS and VITE_API_URL settings.`
    );
  }

  if (!res.ok) {
    const errorMsg = await extractErrorMessage(res, "PDF upload failed");
    throw new Error(errorMsg);
  }

  return res.json();
}

/* ✅ Ask Question */
export async function askQuestion(query: string, doc_id: string) {
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        doc_id,
      }),
    });
  } catch (err: any) {
    throw new Error(
      `Cannot reach backend (${API_BASE_URL}). Check backend health and connection.`
    );
  }

  if (!res.ok) {
    const errorMsg = await extractErrorMessage(res, "Answer generation failed");
    throw new Error(errorMsg);
  }

  return res.json();
}

/* ✅ Health check */
export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (res.ok) return await res.json();
  } catch {
    return { status: "unreachable" };
  }
  return { status: "error" };
}
