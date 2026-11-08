import os
import subprocess
import time
from pathlib import Path

import requests
from pypdf import PdfReader

SERVER_URL = os.getenv("UPRINT_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
DEVICE_TOKEN = os.getenv("UPRINT_DEVICE_TOKEN", "")
REQUEST_HEADERS = {"X-Device-Token": DEVICE_TOKEN} if DEVICE_TOKEN else {}

DOWNLOAD_DIR = Path(os.getenv("UPRINT_WORKER_DOWNLOAD_DIR", "worker_downloads"))
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

PRINTER_NAME = os.getenv("UPRINT_PRINTER_NAME", "Epson_L3210")
SIMULATION_MODE = os.getenv("UPRINT_SIMULATION_MODE", "false").lower() == "true"
POLL_INTERVAL_SECONDS = max(1, int(os.getenv("UPRINT_POLL_INTERVAL_SECONDS", "5")))
MAX_POLL_BACKOFF_SECONDS = max(POLL_INTERVAL_SECONDS, int(os.getenv("UPRINT_MAX_POLL_BACKOFF_SECONDS", "60")))
NETWORK_BACKOFF_MULTIPLIER = 2
REQUEST_TIMEOUT = (10, 60)

SUPPORTED_PRINTERS = {"MF3010", "Epson_L3210"}


def request(method, path, **kwargs):
    """Make an authenticated request and consistently apply timeouts."""
    if not DEVICE_TOKEN:
        print("❌ UPRINT_DEVICE_TOKEN is not configured")
        return None
    try:
        response = requests.request(
            method,
            f"{SERVER_URL}{path}",
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
        return response
    except requests.RequestException as error:
        print(f"🌐 Network request failed: {error}")
        return None


def get_next_job():
    response = request("GET", "/print-queue/next")
    if response is None:
        return None
    if response.status_code != 200:
        print(f"❌ Queue request failed: HTTP {response.status_code}")
        return None
    try:
        return response.json().get("job")
    except ValueError:
        print("❌ Queue returned invalid JSON")
        return None


def download_pdf(file_id):
    response = request("GET", f"/download-pdf/{file_id}")
    if response is None or response.status_code != 200:
        status = response.status_code if response is not None else "network error"
        print(f"❌ PDF download failed: {status}")
        return None

    file_path = DOWNLOAD_DIR / f"{file_id}.pdf"
    try:
        file_path.write_bytes(response.content)
        if not file_path.read_bytes().startswith(b"%PDF-"):
            file_path.unlink(missing_ok=True)
            print("❌ Downloaded file is not a PDF")
            return None
        reader = PdfReader(str(file_path), strict=True)
        if len(reader.pages) < 1:
            file_path.unlink(missing_ok=True)
            print("❌ Downloaded PDF has no pages")
            return None
        return file_path
    except Exception as error:
        file_path.unlink(missing_ok=True)
        print(f"❌ Could not validate downloaded PDF: {error}")
        return None


def update_status(action, order_id, **params):
    response = request("POST", f"/order/{order_id}/{action}", params=params)
    if response is None:
        return False
    if response.status_code != 200:
        print(f"❌ Status update failed: HTTP {response.status_code} {response.text}")
        return False
    return True


def start_printing(order_id):
    return update_status("start-printing", order_id)


def complete_printing(order_id):
    return update_status("complete-printing", order_id)


def fail_printing(order_id, reason="Worker could not submit the job to CUPS"):
    return update_status("fail-printing", order_id, reason=reason)


def print_pdf(pdf_path, job):
    copies = int(job.get("copies", 1))
    printer_name = job.get("printer_name") or PRINTER_NAME

    if printer_name not in SUPPORTED_PRINTERS:
        print("Unsupported printer:", printer_name)
        return False
    if not 1 <= copies <= 50:
        print("Invalid number of copies:", copies)
        return False

    command = ["lp", "-d", printer_name, "-n", str(copies)]
    if job.get("print_type") == "bw":
        command.extend(["-o", "ColorModel=Gray"])
    command.append(str(pdf_path))

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if result.returncode != 0:
            print("CUPS printing failed:", result.stderr)
            return False
        print("CUPS accepted print job:", result.stdout.strip())
        return True
    except (subprocess.TimeoutExpired, OSError) as error:
        print(f"Print submission outcome may be uncertain: {error}")
        return None


def process_job(job):
    order_id = job["order_id"]
    file_id = job["file_id"]
    print(f"📥 Claimed job {order_id}")

    pdf_path = download_pdf(file_id)
    if pdf_path is None:
        # The job has not been sent to the printer. Mark failure if possible;
        # if the network is down, claim expiry will recover it.
        fail_printing(order_id, "PDF download or validation failed")
        return

    if not start_printing(order_id):
        print("Could not confirm printing state; not submitting to printer.")
        return

    if SIMULATION_MODE:
        print("⚠️ Simulation mode: no physical print will be submitted.")
        success = True
    else:
        success = print_pdf(pdf_path, job)

    if success is True:
        if not complete_printing(order_id):
            print("⚠️ CUPS accepted the job, but cloud completion update failed.")
            print("Do not automatically reprint this order; operator review is required.")
    elif success is False:
        fail_printing(order_id)
    else:
        # None means a timeout/ambiguous CUPS result. Do not report failure
        # because the printer may have accepted the job.
        print("⚠️ Print outcome uncertain. Manual operator review required.")


def main():
    print("🖨️ uPrint worker")
    print("Simulation mode:", SIMULATION_MODE)
    print("Server:", SERVER_URL)
    print("Printer:", PRINTER_NAME)

    backoff_seconds = POLL_INTERVAL_SECONDS

    while True:
        job = get_next_job()
        if job is None:
            # Empty queue and temporary API/network errors both wait safely.
            time.sleep(backoff_seconds)
            backoff_seconds = min(
                backoff_seconds * NETWORK_BACKOFF_MULTIPLIER,
                MAX_POLL_BACKOFF_SECONDS,
            )
            continue

        backoff_seconds = POLL_INTERVAL_SECONDS
        try:
            process_job(job)
        except Exception as error:
            # Do not blindly requeue or reprint after an unexpected failure.
            print(f"⚠️ Unexpected job processing error: {error}")
        time.sleep(2)


if __name__ == "__main__":
    main()
