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

# Shared secret for the single authorized Raspberry Pi print worker.
# Keep this value out of source control and configure it in the backend environment.
DEVICE_TOKEN = os.getenv("DEVICE_TOKEN", "")

# Optional Cloudflare R2 (S3-compatible) storage configuration.
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "local").lower()
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL", "")
R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID", "")
R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY", "")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME", "")
R2_REGION = os.getenv("R2_REGION", "auto")
