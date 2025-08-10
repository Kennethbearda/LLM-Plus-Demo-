import openai
import gspread
from typing import TypedDict
from googleapiclient.discovery import Resource
from anthropic import Client
import google.generativeai as genai
from src.constants import GOOGLE_SCOPES

class ClientDict(TypedDict):
    gpt: openai.OpenAI
    claude: Client
    gemini: genai.GenerativeModel
    sheets: gspread.Client
    docs: Resource
    drive: Resource

def auth_gsheets() -> gspread.Client:
    from pathlib import Path
    from google.oauth2.service_account import Credentials

    """
    Authenticate and return a gspread client using service account credentials.
    Looks for credentials_demo.json in the project root.
    """
    # Move up two levels: src/services/auth.py → src → project root
    root_path = Path(__file__).resolve().parents[2]
    cred_path = root_path / "credentials_demo.json"

    creds = Credentials.from_service_account_file(
        str(cred_path),
        scopes=GOOGLE_SCOPES
    )

    client = gspread.authorize(creds)
    return client


def auth_docs():
    from pathlib import Path
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from src.constants import GOOGLE_SCOPES

    # same creds.json path logic as auth_drive()
    root = Path(__file__).resolve().parents[2]
    cred = root / "credentials_demo.json"
    creds = Credentials.from_service_account_file(str(cred), scopes=GOOGLE_SCOPES)
    return build("docs", "v1", credentials=creds)

def auth_drive():
    from pathlib import Path
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from src.constants import GOOGLE_SCOPES

    """
    Authenticate and return a Google Drive client using service account credentials.
    Looks for credentials_demo.json in the project root.
    """
    # Move up two levels: src/services/auth.py → src → project root
    root_path = Path(__file__).resolve().parents[2]
    cred_path = root_path / "credentials_demo.json"

    creds = Credentials.from_service_account_file(
        str(cred_path),
        scopes=GOOGLE_SCOPES
    )

    drive_client = build("drive", "v3", credentials=creds)
    return drive_client

def auth_gpt():
    import os
    from dotenv import load_dotenv
    # Load variables from .env file if it exists
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment or .env file.")

    client = openai.OpenAI(api_key=api_key)
    return client


def auth_gemini():
    import os
    from dotenv import load_dotenv
    import google.generativeai as genai

    # Load variables from .env file if present
    load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY or GEMINI_API_KEY not set in environment or .env file.")

    genai.configure(api_key=api_key)
    return genai


def auth_claude():
    import os
    from dotenv import load_dotenv
    from anthropic import Client  # ✅ correct class

    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set in environment or .env file.")

    return Client(api_key=api_key)  # ✅ correct instantiation


def init_clients() -> ClientDict:
    """Initialize all clients in a functional style, separate from Simplex"""
    return {
        "gpt": auth_gpt(),
        "claude": auth_claude(),
        "gemini": auth_gemini(),
        "sheets": auth_gsheets(),
        "docs": auth_docs(),
        "drive": auth_drive(),
    }