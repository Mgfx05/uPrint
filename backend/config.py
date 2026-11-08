import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{(BACKEND_DIR / 'erb.db').as_posix()}",
)

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))).expanduser().resolve()
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(50 * 1024 * 1024)))

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
