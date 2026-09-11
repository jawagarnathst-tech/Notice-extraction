# PaddleOCR & OpenAI Document Text & Field Extraction Engine

A clean, modular Python application that extracts raw text and 2D visual layout from government notices and PDFs using **PaddleOCR**, followed by strict structured business field extraction using the **OpenAI API**.

---

## 1. Pipeline Architecture

```text
======================= PHASE 1: OCR & LAYOUT =======================
PDF / Image
    ↓
PaddleOCR (CPU)
    ↓
Raw OCR JSON (output/<name>_raw_ocr.json)
    ↓
2D Coordinate Spatial Reconstruction
    ↓
Layout-preserved Text (output/<name>_layout.txt)

==================== PHASE 2: STRUCTURED AI EXTRACTION ====================
Layout-preserved Text
    ↓
OpenAI API (gpt-4o-mini / gpt-4o)
    ↓
Pydantic Schema Validation & Business Rule Enforcement
    ↓
Strict JSON Output (output/<name>_extracted_fields.json)
```

---

## 2. Project Structure

```text
Notice Extraction/
│
├── input/
│   ├── <notice_files>.pdf         # Input tax notice PDFs or images
│
├── output/
│   ├── <name>_layout.txt          # Reconstructed text with original visual columns & spacing
│   ├── <name>_raw_ocr.json        # Full raw OCR detections with coordinates & confidence
│   ├── <name>_extracted_fields.json # Strict 7-field OpenAI extraction JSON
│   └── debug/
│       ├── <name>_page_1.png      # Rendered page image
│       └── <name>_page_1_ocr.png  # Image with bounding box visual overlay
│
├── src/
│   ├── __init__.py
│   ├── config.py                  # Environment & OPENAI_API_KEY loader
│   ├── models.py                  # Strict Pydantic models for extracted fields
│   ├── file_service.py            # Input validation and file type checking
│   ├── pdf_service.py             # PyMuPDF-based PDF to image rendering (200 DPI)
│   ├── ocr_service.py             # PaddleOCR engine runner & bounding box drawer
│   ├── layout_service.py          # 2D coordinate-based spatial layout reconstruction
│   ├── ai_extraction_service.py   # OpenAI field extraction engine
│   └── output_service.py          # Console display & file persistence
│
├── main.py                        # CLI application entrypoint
├── requirements.txt               # Pinned, tested dependencies
├── .env                           # OpenAI API Key configuration (git-ignored)
├── .env.example                   # Template configuration
├── .gitignore
└── README.md
```

---

## 3. Setup & Environment

### Step 1: Create and Activate Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Configure `.env`

Create a `.env` file containing only your OpenAI API key:

```ini
OPENAI_API_KEY=your_openai_api_key_here
```

---

## 4. Usage

### Run End-to-End Extraction (Phase 1 + Phase 2)

```powershell
python main.py "input/Tax Notices - Sample (3)/Al_Failure To File W-2'S Penalty Notice.pdf"
```

### Optional CLI Arguments

| Argument | Default | Description |
|---|---|---|
| `--skip-ai` | `False` | Run Phase 1 OCR only without calling OpenAI. |
| `--model` | `gpt-4o-mini` | Specify OpenAI model (`gpt-4o-mini`, `gpt-4o`, etc.). |
| `--print-coords` | `False` | Print detected OCR bounding box coordinates to console. |
| `--no-debug` | `False` | Disable generation of visual bounding box debug images. |
| `--conf-threshold` | `0.80` | Score below which lines are marked as low confidence. |

Example running OCR-only:
```powershell
python main.py "input/Tax Notices - Sample (3)/Notice of Tax Due.pdf" --skip-ai
```

---

## 5. Output Files & Schema

For every document processed, the output files saved in [`output/`](file:///c:/Users/c1822/Notice%20Extraction/output) are:

### 1. `output/<filename>_extracted_fields.json`
Strict 7-field structured output validated by Pydantic:
```json
{
  "account": "PHARMALA SPECIALTY PHARMACY LLC",
  "country": "United States of America",
  "agency": "Alabama",
  "agency_type": "Department",
  "department": "Department of Revenue",
  "classification": "Withholding Tax Account",
  "notice_type": "Withholding Tax Account"
}
```

### 2. `output/<filename>_layout.txt`
Reconstructed document text preserving columns, headers, tables, and blank lines based on OCR coordinates.

*(Raw OCR coordinates JSON and visual debug images can be optionally generated with `--save-raw-ocr` or `--debug`).*
 