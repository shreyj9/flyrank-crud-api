"""Supabase Auth client configured only through environment variables."""

from __future__ import annotations

import os

from dotenv import load_dotenv
from supabase import Client, create_client

load_dotenv()


def _required_environment_value(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("your-") or value.startswith("your_"):
        raise RuntimeError(
            f"{name} is not configured. Add the real value to the git-ignored .env file."
        )
    return value


SUPABASE_URL = _required_environment_value("SUPABASE_URL")
SUPABASE_KEY = _required_environment_value("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
