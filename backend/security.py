import secrets

from fastapi import Header, HTTPException

from config import DEVICE_TOKEN


def require_print_device(x_device_token: str = Header(default="")) -> None:
    if not DEVICE_TOKEN:
        raise HTTPException(
            status_code=503,
            detail="Print device authentication is not configured",
        )

    if not secrets.compare_digest(x_device_token, DEVICE_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid print device credentials")
