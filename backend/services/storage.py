from pathlib import Path
from typing import BinaryIO

from config import UPLOAD_DIR


class LocalPDFStorage:
    """Local filesystem implementation; cloud adapters can implement this API."""

    def path_for(self, file_id: str) -> Path:
        return UPLOAD_DIR / f"{file_id}.pdf"

    def save(self, file_id: str, source: BinaryIO) -> Path:
        destination = self.path_for(file_id)
        with destination.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
        return destination

    def exists(self, file_id: str) -> bool:
        return self.path_for(file_id).is_file()

    def delete(self, file_id: str) -> None:
        path = self.path_for(file_id)
        if path.exists():
            path.unlink()


pdf_storage = LocalPDFStorage()
