import logging
import os
import re

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from ingestion.parser import parse_pdf
from ingestion.uploader import upload_to_qdrant

from ingestion.table_parser import extract_tables
from ingestion.figure_extractor import extract_figures

from retrieval.search import retrieve
from llm.generator import generate_answer

from storage.qdrant_client import (
    setup_collection,
    client,
    COLLECTION_NAME,
)

from models import AskRequest, AskResponse


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

TEMP_DIR = "temp"
EXTRACTED_DIR = "extracted"

MAX_UPLOAD_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB

ALLOWED_CONTENT_TYPES = {
    "application/pdf"
}


# ============================================================
# CREATE DIRECTORIES
# ============================================================

# These directories must exist before StaticFiles is mounted.
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(EXTRACTED_DIR, exist_ok=True)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="GoRag Backend",
    version="1.0",
    description="Multimodal Agentic RAG Pipeline (Text + Tables + Figures)",
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

# Read additional origins from environment variables if present
configured_origins = [
    # Production frontend
    "https://gorag.vercel.app",
    # Local development
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

env_frontend_url = os.getenv("FRONTEND_URL")
if env_frontend_url:
    for url in env_frontend_url.split(","):
        cleaned = url.strip()
        if cleaned and cleaned not in configured_origins:
            configured_origins.append(cleaned)

env_allowed_origins = os.getenv("ALLOWED_ORIGINS")
if env_allowed_origins:
    for url in env_allowed_origins.split(","):
        cleaned = url.strip()
        if cleaned and cleaned not in configured_origins:
            configured_origins.append(cleaned)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins,
    allow_origin_regex=r"^https://.*\.vercel\.app$|^http://(localhost|127\.0\.0\.1):\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# STATIC FILES
# ============================================================

# Allows extracted images/figures to be accessed through:
# https://gorag-backend.onrender.com/extracted/figures/filename.png

app.mount(
    "/extracted",
    StaticFiles(directory=EXTRACTED_DIR),
    name="extracted",
)


# ============================================================
# STARTUP EVENT
# ============================================================

@app.on_event("startup")
def startup():
    logger.info("FastAPI starting up...")

    try:
        setup_collection()
        logger.info("Qdrant collection and indexes ready!")
    except Exception as e:
        logger.warning(
            "Qdrant setup during startup failed: %s. "
            "Server will remain online, but vector queries may fail until Qdrant is connected.",
            e,
        )


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def home():
    return {
        "status": "GoRag Backend Running",
        "docs": "/docs",
        "health": "/health",
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():
    gemini_key_set = bool(os.getenv("GEMINI_API_KEY"))
    qdrant_url_set = bool(os.getenv("QDRANT_URL"))
    return {
        "status": "healthy",
        "gemini_configured": gemini_key_set,
        "qdrant_configured": qdrant_url_set,
    }



# ============================================================
# FILENAME SANITIZATION
# ============================================================

def _sanitize_filename(filename: str) -> str:
    """
    Collapse filename to a safe basename.

    Removes:
    - directory traversal
    - special characters
    - leading dots
    """

    name = os.path.basename(filename or "").strip()

    name = re.sub(
        r"[^A-Za-z0-9._-]",
        "_",
        name,
    )

    name = name.lstrip(".")

    return name


# ============================================================
# SAFE FILE REMOVAL
# ============================================================

def _safe_remove(path: str) -> None:
    """
    Safely remove a file.
    """

    try:

        if path and os.path.exists(path):
            os.remove(path)

    except OSError:

        logger.warning(
            "Could not remove temp file %s",
            path,
            exc_info=True,
        )


# ============================================================
# PDF INGESTION
# ============================================================

def _ingest_pdf(
    pdf_path: str,
    doc_id: str,
) -> int:
    """
    Perform all CPU-bound PDF ingestion work.

    Includes:

    1. PDF text extraction
    2. Table extraction
    3. Figure extraction
    4. Qdrant upload
    """

    # ----------------------------------------
    # Extract normal text
    # ----------------------------------------

    blocks = parse_pdf(pdf_path)

    # ----------------------------------------
    # Extract tables
    # ----------------------------------------

    try:
        table_blocks = extract_tables(pdf_path)
        blocks.extend(table_blocks)
    except Exception as e:
        logger.warning("Table extraction failed for %s (continuing): %s", doc_id, e)

    # ----------------------------------------
    # Extract figures
    # ----------------------------------------

    try:
        figure_blocks = extract_figures(
            pdf_path,
            doc_id,
        )
        blocks.extend(figure_blocks)
    except Exception as e:
        logger.warning("Figure extraction failed for %s (continuing): %s", doc_id, e)

    if not blocks:
        logger.warning("No blocks extracted from PDF %s. Inserting placeholder.", doc_id)
        blocks.append({
            "type": "text",
            "page": 1,
            "content": f"Document {doc_id} contains no readable text or visuals.",
        })

    logger.info(
        "Total extracted blocks = %d",
        len(blocks),
    )

    # ----------------------------------------
    # Upload embeddings / blocks to Qdrant
    # ----------------------------------------

    upload_to_qdrant(
        blocks,
        doc_id,
    )

    return len(blocks)


# ============================================================
# UPLOAD ENDPOINT
# ============================================================

@app.post("/upload")
async def upload_pdf(file: UploadFile):

    logger.info(
        "Upload request received: filename=%s content_type=%s",
        file.filename,
        file.content_type,
    )

    # ========================================================
    # SANITIZE FILENAME
    # ========================================================

    safe_name = _sanitize_filename(
        file.filename
    )

    if not safe_name:
        raise HTTPException(
            status_code=400,
            detail="Invalid filename.",
        )

    # ========================================================
    # CHECK FILE EXTENSION
    # ========================================================

    if not safe_name.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted.",
        )

    # ========================================================
    # CHECK CONTENT TYPE
    # ========================================================

    if (
        file.content_type
        and file.content_type not in ALLOWED_CONTENT_TYPES
    ):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted.",
        )

    # ========================================================
    # CREATE DOCUMENT ID
    # ========================================================

    doc_id = safe_name

    pdf_path = os.path.join(
        TEMP_DIR,
        doc_id,
    )

    # ========================================================
    # SAVE UPLOADED FILE
    # ========================================================

    size = 0

    try:

        with open(
            pdf_path,
            "wb",
        ) as buffer:

            while True:

                chunk = await file.read(
                    1024 * 1024
                )

                if not chunk:
                    break

                size += len(chunk)

                # --------------------------------------------
                # MAX SIZE CHECK
                # --------------------------------------------

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

        logger.exception(
            "Failed to save uploaded file %s",
            doc_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to save uploaded file.",
        )

    finally:

        await file.close()

    logger.info(
        "PDF uploaded: %s (%d bytes)",
        doc_id,
        size,
    )

    # ========================================================
    # PROCESS PDF
    # ========================================================

    try:

        block_count = await run_in_threadpool(
            _ingest_pdf,
            pdf_path,
            doc_id,
        )

    except Exception as exc:

        _safe_remove(pdf_path)

        logger.exception(
            "Failed to process PDF %s: %s",
            doc_id,
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to process uploaded PDF: {str(exc)}",
        )

    # ========================================================
    # CHECK QDRANT
    # ========================================================

    try:

        count = client.count(
            collection_name=COLLECTION_NAME,
            exact=True,
        )

        logger.info(
            "Points after upload = %d",
            count.count,
        )

    except Exception:

        logger.exception(
            "Failed to check Qdrant point count"
        )


    # ========================================================
    # REMOVE TEMP PDF
    # ========================================================

    _safe_remove(pdf_path)


    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "uploaded",
        "doc_id": doc_id,
        "blocks": block_count,
    }


# ============================================================
# ASK ENDPOINT
# ============================================================

@app.post(
    "/ask",
    response_model=AskResponse,
)
async def ask(request: AskRequest):

    query = request.query
    doc_id = request.doc_id

    logger.info(
        "Ask request received: query=%r doc_id=%r",
        query,
        doc_id,
    )

    # ========================================================
    # RETRIEVAL
    # ========================================================

    try:

        context, visuals, citations = (
            await run_in_threadpool(
                retrieve,
                query,
                doc_id,
            )
        )

    except Exception:

        logger.exception(
            "Retrieval failed for doc_id=%s",
            doc_id,
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve context from the document.",
        )

    # ========================================================
    # LOG RETRIEVAL RESULT
    # ========================================================

    logger.info(
        "Retrieved context length=%d visuals=%d citations=%s",
        len(context),
        len(visuals),
        citations,
    )

    # ========================================================
    # NO CONTEXT FOUND
    # ========================================================

    if not context and not visuals:

        return AskResponse(
            answer="No relevant information found.",
            citations=[],
            supporting_visuals=[],
            doc_id=doc_id,
        )

    # ========================================================
    # GENERATE ANSWER
    # ========================================================

    try:

        answer = await run_in_threadpool(
            generate_answer,
            query,
            context,
            citations,
        )

    except Exception as exc:

        logger.exception(
            "Answer generation failed for doc_id=%s: %s",
            doc_id,
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(exc)}",
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return AskResponse(
        answer=answer,
        citations=citations,
        supporting_visuals=visuals,
        doc_id=doc_id,
    )
