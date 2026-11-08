from pathlib import Path

from config import UPLOAD_DIR


class LocalPDFStorage:
    """Store PDFs directly on the Raspberry Pi's local filesystem."""

    def __init__(self):
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_id: str, source_path: Path) -> None:
        destination = self.path_for(file_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        source_path.replace(destination)

    def path_for(self, file_id: str) -> Path:
        return UPLOAD_DIR / f"{file_id}.pdf"

    def materialize(self, file_id: str) -> Path:
        path = self.path_for(file_id)
        if not path.is_file():
            raise FileNotFoundError(file_id)
        return path

    def delete(self, file_id: str) -> None:
        self.path_for(file_id).unlink(missing_ok=True)


pdf_storage = LocalPDFStorage()
