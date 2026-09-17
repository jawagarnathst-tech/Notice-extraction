import os
import shutil
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="paddle.*")

from main import run_pipeline
from src.layout_service import LayoutConfig

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

@app.post("/api/extract")
async def extract_notice(request: Request, file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    processed_by = request.headers.get("X-Processed-By") or "SYSTEM"

    # Create a temporary directory for processing
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / file.filename

    try:
        # Save the uploaded file temporarily
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        if _log_uni:
            _log_uni("notice-extraction", "extract", file.filename, "STARTED", "Processing Notice", processed_by=processed_by)

        # Configure default layout
        layout_config = LayoutConfig()

        # Run the extraction pipeline
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
            if _log_uni:
                _log_uni("notice-extraction", "extract", file.filename, "FAILED", "AI extraction returned no result.", processed_by=processed_by)
            raise HTTPException(status_code=500, detail="AI extraction failed or returned no result.")

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

        if _log_uni:
            _log_uni("notice-extraction", "extract", file.filename, "SUCCESS", f"Extracted {doc_result.total_pages} pages", processed_by=processed_by)

        return response

    except Exception as e:
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
