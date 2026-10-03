# GoRag — Multimodal PDF RAG Application (Text + Tables + Figures)

GoRag is an end-to-end multimodal Retrieval-Augmented Generation (RAG) system that processes PDFs, extracts text chunks, tables, and embedded figures, indexes them into a high-performance Qdrant vector database, and generates grounded answers with inline visual evidence using Google Gemini.

---

## 🏗️ Architecture

- **Frontend**: React 18 + Vite + Tailwind CSS + Framer Motion (Hosted on **Vercel**)
- **Backend API**: FastAPI + Uvicorn + PyMuPDF + Sentence-Transformers (Hosted on **Render**)
- **Vector Database**: Qdrant Cloud (512-dimensional vector collection `visrag_multimodal`)
- **LLM / Grounding**: Google Gemini (`gemini-1.5-flash`) via Google Generative AI

```
┌──────────────────┐               ┌──────────────────────────┐
│  React Frontend  │ ──(HTTP/REST)─▶  FastAPI Backend (Render)│
│     (Vercel)     │               └─────────────┬────────────┘
└──────────────────┘                             │
                                  ┌──────────────┴──────────────┐
                                  │                             │
                                  ▼                             ▼
                      ┌──────────────────────┐      ┌─────────────────────────┐
                      │  Qdrant Vector Cloud │      │  Google Gemini 1.5 Flash│
                      │ (visrag_multimodal)  │      │   (AI Answer & Citations)
                      └──────────────────────┘      └─────────────────────────┘
```

---

## 🚀 Deployment Guide

### 1. Backend on Render

1. Go to [Render Dashboard](https://dashboard.render.com/) and click **New +** -> **Web Service**.
2. Connect your GitHub repository: `baibhav16/GoRag`.
3. Configure the service settings:
   - **Name**: `gorag-api`
   - **Region**: Closest to your users (e.g., Singapore, Frankfurt, Oregon)
   - **Branch**: `main`
   - **Root Directory**: Leave blank (uses repo root)
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn app:app --app-dir Backend --host 0.0.0.0 --port $PORT
     ```
   - **Health Check Path**: `/health`

4. Add the **Environment Variables** in Render:
   | Key | Value | Description |
   | --- | --- | --- |
   | `PYTHON_VERSION` | `3.11.10` | Python version |
   | `GEMINI_API_KEY` | `AIzaSy...` | Your Google AI Studio API key |
   | `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model for answer generation |
   | `QDRANT_URL` | `https://<cluster-id>.<region>.gcp.cloud.qdrant.io:6333` | Qdrant Cloud URL |
   | `QDRANT_API_KEY` | `your_qdrant_api_key` | Qdrant Cloud API key |
   | `FRONTEND_URL` | `https://your-app.vercel.app` | Your Vercel frontend URL |
   | `ENABLE_CLIP` | `false` | Keeps memory < 300MB on Render Free Tier |

5. Click **Create Web Service**. Note your Render URL (e.g., `https://gorag-api.onrender.com`).

---

### 2. Frontend on Vercel

1. Go to [Vercel Dashboard](https://vercel.com/) and click **Add New...** -> **Project**.
2. Import the `baibhav16/GoRag` repository.
3. Configure the project:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click *Edit* and select **`Frontend`**
   - **Build Command**: `npm run build` (or leave default)
   - **Output Directory**: `dist` (or leave default)
4. Add the **Environment Variable**:
   | Key | Value |
   | --- | --- |
   | `VITE_API_URL` | `https://gorag-api.onrender.com` (Your Render URL, **no trailing slash**) |

5. Click **Deploy**.
6. When deployment finishes, copy your Vercel URL (e.g., `https://gorag-xxx.vercel.app`).
7. *(Optional)* Add your Vercel URL to the `FRONTEND_URL` variable in your Render dashboard (Render automatically allows all `*.vercel.app` domains by default!).

---

## 🛠️ Local Development

### 1. Backend Setup
```bash
# From repository root:
cd Backend
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r ../requirements.txt

# Create .env from .env.example
copy .env.example .env
# Edit .env with your QDRANT_URL, QDRANT_API_KEY, and GEMINI_API_KEY

# Start backend on port 8000:
uvicorn app:app --reload --port 8000
```
API Documentation will be live at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup
```bash
# In a new terminal:
cd Frontend
npm install

# Create .env from .env.example
copy .env.example .env
# Default points to http://127.0.0.1:8000

# Start frontend:
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🔍 Troubleshooting & Common Issues

### 1. Render Free Tier Cold Starts
Render free services spin down after 15 minutes of inactivity. When a new request arrives, Render takes **45–60 seconds** to boot the container. If the frontend shows a connection timeout or waking-up message, wait 1 minute and retry.

### 2. Missing `VITE_API_URL` on Vercel
Vite bundles environment variables into the static JavaScript at **build time**. If you set or change `VITE_API_URL` in Vercel, you must go to **Deployments** and click **Redeploy** for the change to take effect.

### 3. Out-Of-Memory (OOM / Code 137) on Render
Render's free tier has a 512MB RAM ceiling. Loading CLIP (`openai/clip-vit-base-patch32`) requires 600MB+ alone. Keep `ENABLE_CLIP=false` (the default) so the backend runs on lightweight `all-MiniLM-L6-v2` embeddings (~150MB total RAM).

### 4. Ghostscript & OpenCV Errors
Table extraction previously depended on `camelot-py`, which required system-level `ghostscript` binaries not present in Render. GoRag now uses native `PyMuPDF` (`page.find_tables()`), eliminating all external binary dependencies.
