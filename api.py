import os
import shutil
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="paddle.*")

from main import run_pipeline
from src.layout_service import LayoutConfig

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
async def extract_notice(file: UploadFile = File(...)) -> Dict[str, Any]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    # Create a temporary directory for processing
    temp_dir = Path("temp_uploads")
    temp_dir.mkdir(exist_ok=True)

    file_path = temp_dir / file.filename

    try:
        # Save the uploaded file temporarily
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

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
            ai_model=os.getenv("AI_MODEL", "gpt-4o-mini"),
        )

        if not ai_result:
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

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temporary file
        if file_path.exists():
            file_path.unlink()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
