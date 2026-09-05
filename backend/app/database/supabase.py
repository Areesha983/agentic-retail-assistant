import os
from pathlib import Path

from dotenv import load_dotenv
from supabase import create_client, Client


# Project root: D:\agentic_retail
BASE_DIR = Path(__file__).resolve().parents[3]

# Load .env from project root
load_dotenv(BASE_DIR / ".env")


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Supabase credentials are missing from .env")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)