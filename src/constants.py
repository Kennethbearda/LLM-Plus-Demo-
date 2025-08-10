import os
from pathlib import Path

# ── Project root ───────────────────────────────────────────────────────────────
# constants.py is in src/, so one level up is LLM-PLUS
ROOT = Path(__file__).resolve().parents[1]
print(f"DEBUG: __file__ = {__file__}")
print(f"DEBUG: ROOT = {ROOT}")

# ── Download directory ─────────────────────────────────────────────────────────
# Use $DOWNLOAD_DIR if set, otherwise default to "<project root>/downloads"
DOWNLOAD_DIR = Path(os.getenv("DOWNLOAD_DIR", ROOT / "downloads"))
print(f"DEBUG: DOWNLOAD_DIR = {DOWNLOAD_DIR}")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── Google Sheets & Drive IDs ─────────────────────────────────────────────────
OVERSEER_SHEET_ID  = "1yKUTzp94G3SJKqC22f1vunj_-6PrGIzkkV9k7vLPivw"
UPLOADS_FOLDER_ID  = "1Op6_FOYSN587c9J74Amp_0uEgnr402uC"
ARCHIVE_FOLDER_ID  = "13U-5zoU1dmB1_AjYqmht6gIDGW5zt20D"
TEMPLATES_FOLDER_ID = "1DJywEtNnjs2jutx28QbzNiLuohFHPnCU"

# ── Google Docs ID for write_to_doc() ─────────────────────────────────────────
DOCUMENT_ID = "1HH_8r0_KHP0KLgyt-jLMJZNar3BO0tuVTUmb7Z_bnIk"

# ── Google API scopes ──────────────────────────────────────────────────────────
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents"  # for Google Docs
]

# Mapping of cell addresses to their logical meaning in the control panel
SHEET_CELL_MAP = {
    "C1": "system_state",
    "C2": "last_check_time",
    "C8": "toggle_button",           # Toggle Button (start/stop)
    "C9": "template_file_name",      # Template File Name
    "C10": "run_mode",               # Run Mode
    "C11": "run_duration_hours",    # Run Duration (Hours)
    "C12": "computer_vision_mode",  # Computer Vision Mode
    # Add more if needed for other settings
}

# Reverse mapping for getting cell references
CELL_REF_MAP = {v: k for k, v in SHEET_CELL_MAP.items()}