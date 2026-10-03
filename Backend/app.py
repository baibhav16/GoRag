import logging
import os
import re

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from ingestion.parser import parse_pdf
from ingestion.uploader import upload_to_qdrant

from ingestion.table_parser import extract_tables
from ingestion.figure_extractor import extract_figures

from retrieval.search import retrieve
from llm.generator import generate_answer
from storage.qdrant_client import setup_collection, client, COLLECTION_NAME

from models import AskRequest, AskResponse

origins = [
    "https://gorag.vercel.app",
    "http://localhost:5173",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


TEMP_DIR = "temp"
EXTRACTED_DIR = "extracted"
MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# ✅ Directories must exist BEFORE StaticFiles is mounted below — Starlette's
# StaticFiles raises RuntimeError at import time if the directory is missing,
# which previously crashed the app on a fresh clone (extracted/ didn't exist yet).
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)


# -------------------------------
# ✅ FASTAPI APP
# -------------------------------
app = FastAPI(
    title="GoRag Backend",
    version="1.0",
    description="Multimodal Agentic RAG Pipeline (Text + Tables + Figures)"
)

# ✅ Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Serve extracted visuals
app.mount("/extracted", StaticFiles(directory=EXTRACTED_DIR), name="extracted")


# -------------------------------
# ✅ STARTUP EVENT
# -------------------------------
@app.on_event("startup")
def startup():
    logger.info("FastAPI startup...")
    setup_collection()
    logger.info("Qdrant ready!")


# -------------------------------
# ✅ ROOT
# -------------------------------
@app.get("/")
def home():
    return {"status": "GoRag Backend Running"}


def _sanitize_filename(filename: str) -> str:
    """Collapse to a safe basename: strips directories and traversal segments."""
    name = os.path.basename(filename or "").strip()
    name = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    name = name.lstrip(".")
    return name


def _safe_remove(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        logger.warning("Could not remove temp file %s", path, exc_info=True)


def _ingest_pdf(pdf_path: str, doc_id: str) -> int:
    """✅ All CPU-bound ingestion work (PyMuPDF, Camelot, embeddings) — run in
    a threadpool by the caller so it doesn't block the asyncio event loop."""
    blocks = parse_pdf(pdf_path)
    blocks.extend(extract_tables(pdf_path))
    blocks.extend(extract_figures(pdf_path, doc_id))
    logger.info("Total extracted blocks = %d", len(blocks))
    upload_to_qdrant(blocks, doc_id)
    return len(blocks)


# -------------------------------
# ✅ UPLOAD ENDPOINT
# -------------------------------
@app.post("/upload")
async def upload_pdf(file: UploadFile):

    safe_name = _sanitize_filename(file.filename)

    if not safe_name.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    if file.content_type and file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    doc_id = safe_name
    pdf_path = os.path.join(TEMP_DIR, doc_id)

    size = 0
    try:
        with open(pdf_path, "wb") as buffer:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="File too large (max 25MB).",
                    )
                buffer.write(chunk)
    except HTTPException:
        _safe_remove(pdf_path)
        raise
    except OSError:
        _safe_remove(pdf_path)
        logger.exception("Failed to save uploaded file %s", doc_id)
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.")

    logger.info("PDF uploaded: %s", doc_id)

    try:
        block_count = await run_in_threadpool(_ingest_pdf, pdf_path, doc_id)
    except Exception:
        _safe_remove(pdf_path)
        logger.exception("Failed to process PDF %s", doc_id)
        raise HTTPException(status_code=500, detail="Failed to process the uploaded PDF.")

    count = client.count(collection_name=COLLECTION_NAME, exact=True)
    logger.info("Points after upload = %d", count.count)

    return {
        "status": "uploaded",
        "doc_id": doc_id,
        "blocks": block_count,
    }


# -------------------------------
# ✅ ASK ENDPOINT
# -------------------------------
@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):

    query = request.query
    doc_id = request.doc_id

    logger.info("Ask request received: query=%r doc_id=%r", query, doc_id)

    try:
        context, visuals, citations = await run_in_threadpool(retrieve, query, doc_id)
    except Exception:
        logger.exception("Retrieval failed for doc_id=%s", doc_id)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve context from the document.",
        )

    logger.info(
        "Retrieved context length=%d visuals=%d citations=%s",
        len(context), len(visuals), citations,
    )

    if not context and not visuals:
        return AskResponse(
            answer="No relevant information found.",
            citations=[],
            supporting_visuals=[],
            doc_id=doc_id,
        )

    try:
        answer = await run_in_threadpool(generate_answer, query, context, citations)
    except Exception:
        logger.exception("Answer generation failed for doc_id=%s", doc_id)
        raise HTTPException(status_code=500, detail="Failed to generate an answer.")

    return AskResponse(
        answer=answer,
        citations=citations,
        supporting_visuals=visuals,
        doc_id=doc_id,
    )
