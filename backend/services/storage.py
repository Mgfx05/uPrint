import os
import tempfile
from pathlib import Path

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from config import (
    UPLOAD_DIR, STORAGE_BACKEND, R2_ENDPOINT_URL, R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME, R2_REGION,
)


class LocalPDFStorage:
    """Local filesystem storage for development and offline testing."""

    def save_file(self, file_id: str, source_path: Path) -> None:
        destination = UPLOAD_DIR / f"{file_id}.pdf"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source_path.read_bytes())

    def materialize(self, file_id: str) -> Path:
        path = UPLOAD_DIR / f"{file_id}.pdf"
        if not path.is_file():
            raise FileNotFoundError(file_id)
        return path

    def delete(self, file_id: str) -> None:
        (UPLOAD_DIR / f"{file_id}.pdf").unlink(missing_ok=True)


class R2PDFStorage:
    """Private Cloudflare R2 bucket using its S3-compatible API."""

    def __init__(self):
        required = {
            "R2_ENDPOINT_URL": R2_ENDPOINT_URL,
            "R2_ACCESS_KEY_ID": R2_ACCESS_KEY_ID,
            "R2_SECRET_ACCESS_KEY": R2_SECRET_ACCESS_KEY,
            "R2_BUCKET_NAME": R2_BUCKET_NAME,
        }
        missing = [key for key, value in required.items() if not value]
        if missing:
            raise RuntimeError("Missing R2 configuration: " + ", ".join(missing))
        self.bucket = R2_BUCKET_NAME
        self.client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY_ID,
            aws_secret_access_key=R2_SECRET_ACCESS_KEY,
            region_name=R2_REGION,
        )

    def save_file(self, file_id: str, source_path: Path) -> None:
        self.client.upload_file(
            str(source_path), self.bucket, f"pdfs/{file_id}.pdf",
            ExtraArgs={"ContentType": "application/pdf"},
        )

    def materialize(self, file_id: str) -> Path:
        fd, name = tempfile.mkstemp(prefix="uprint-", suffix=".pdf")
        os.close(fd)
        path = Path(name)
        try:
            self.client.download_file(self.bucket, f"pdfs/{file_id}.pdf", str(path))
            return path
        except (BotoCoreError, ClientError):
            path.unlink(missing_ok=True)
            raise FileNotFoundError(file_id)

    def delete(self, file_id: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=f"pdfs/{file_id}.pdf")


def build_storage():
    if STORAGE_BACKEND == "local":
        return LocalPDFStorage()
    if STORAGE_BACKEND == "r2":
        return R2PDFStorage()
    raise RuntimeError("STORAGE_BACKEND must be 'local' or 'r2'")


pdf_storage = build_storage()
