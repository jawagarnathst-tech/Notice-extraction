import logging
import os
import shutil
import sys
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="paddle.*")

from main import run_pipeline, configure_logging
from src.layout_service import LayoutConfig
from src.excel_export_service import ExcelExportService

# Configure application-wide logging so all logs appear in the terminal
configure_logging()
logger = logging.getLogger("api")

try:
    from database.poc_db import log_universal as _log_uni
except ImportError:
    _log_uni = None

load_dotenv()

app = FastAPI(title="Notice Extraction API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the exact origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Excel export service (loaded once at startup)
_excel_export_service = ExcelExportService()
logger.info("Notice Extraction API initialized and ready.")


class ExcelExportRequest(BaseModel):
    """Request body for the Excel export endpoint."""
    extracted_data: Dict[str, Any]
    file_name: Optional[str] = "notice"


@app.post("/api/extract")
async def extract_notice(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    processed_by = request.headers.get("X-Processed-By") or "SYSTEM"

    logger.info("==================================================")
    logger.info("--> [API] Received extraction request for file: %s (Processed by: %s)", file.filename, processed_by)
    logger.info("==================================================")

    # Create a temporary directory for processing
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / file.filename

    try:
        # Save the uploaded file temporarily
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        logger.info("Saved temporary upload to: %s (%d bytes)", file_path, file_path.stat().st_size)

        if _log_uni:
            _log_uni("notice-extraction", "extract", file.filename, "STARTED", "Processing Notice", processed_by=processed_by)

        # Configure default layout
        layout_config = LayoutConfig()

        # Run the extraction pipeline
        logger.info("--> [API] Executing extraction pipeline (OCR + AI)...")
        doc_result, ai_result = run_pipeline(
            file_path=file_path,
            layout_config=layout_config,
            conf_threshold=0.80,
            save_debug=False,
            save_raw_ocr=False,
            print_coordinates=False,
            lang="en",
            run_ai=True,
            ai_model=os.getenv("AI_MODEL", "gpt-4o"),
        )

        if not ai_result:
            logger.error("--> [API] AI extraction returned no result for %s", file.filename)
            if _log_uni:
                _log_uni("notice-extraction", "extract", file.filename, "FAILED", "AI extraction returned no result.", processed_by=processed_by)
            raise HTTPException(status_code=500, detail="AI extraction failed or returned no result.")

        logger.info("--> [API] Pipeline completed successfully: %d pages, %d lines", doc_result.total_pages, doc_result.total_lines)

        # Format the response
        response = {
            "status": "success",
            "document": {
                "file_name": doc_result.file_name,
                "total_pages": doc_result.total_pages,
                "total_lines": doc_result.total_lines,
                "average_confidence": doc_result.average_confidence,
            },
            "extracted_data": ai_result.to_strict_dict(),
        }

        # Also save the Excel extraction tracker to the output folder
        try:
            base_name = Path(file.filename).stem
            logger.info("--> [API] Generating Excel extraction tracker for %s...", file.filename)
            excel_bytes = _excel_export_service.generate(
                extracted_data=ai_result.to_strict_dict(),
                file_name=file.filename,
            )
            output_dir = Path("output")
            output_dir.mkdir(exist_ok=True)
            excel_path = output_dir / f"{base_name}_extraction_tracker.xlsx"
            excel_path.write_bytes(excel_bytes)
            logger.info("--> [API] Excel tracker saved to: %s (%d bytes)", excel_path, len(excel_bytes))
        except Exception as excel_err:
            logger.warning("--> [API] Excel output generation failed (non-fatal): %s", excel_err)

        if _log_uni:
            _log_uni("notice-extraction", "extract", file.filename, "SUCCESS", f"Extracted {doc_result.total_pages} pages", processed_by=processed_by)

        logger.info("--> [API] Request completed successfully for %s", file.filename)
        return response

    except Exception as e:
        logger.error("--> [API] Extraction failed for %s: %s", file.filename if file else "unknown", e, exc_info=True)
        if _log_uni:
            _log_uni("notice-extraction", "extract", file.filename if file else "unknown", "FAILED", str(e), processed_by=processed_by)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary file
        if file_path.exists():
            file_path.unlink()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/export-excel")
async def export_excel(payload: ExcelExportRequest):
    """
    Generate a filled Excel workbook from extracted notice data.

    Accepts the extracted_data dict and returns the populated .xlsx template
    as a downloadable file.
    """
    try:
        excel_bytes = _excel_export_service.generate(
            extracted_data=payload.extracted_data,
            file_name=payload.file_name or "notice",
        )

        # Build a clean download filename
        base_name = Path(payload.file_name or "notice").stem
        download_name = f"{base_name}_extraction_tracker.xlsx"

        return StreamingResponse(
            BytesIO(excel_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{download_name}"',
            },
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=f"Template error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export failed: {e}")
