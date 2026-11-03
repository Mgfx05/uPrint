import requests
import time
import subprocess
from pathlib import Path


# ============================================================
# ERB PRINT WORKER
# ============================================================

SERVER_URL = "http://127.0.0.1:8000"

DOWNLOAD_DIR = Path("worker_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

PRINTER_NAME = "Epson_L3210"

SIMULATION_MODE = False


# ============================================================
# GET NEXT PRINT JOB
# ============================================================

def get_next_job():

    try:

        response = requests.get(
            f"{SERVER_URL}/print-queue/next"
        )

        if response.status_code != 200:

            print("❌ Could not check print queue")

            return None

        data = response.json()

        if data.get("job") is None:

            return None

        return data["job"]

    except requests.exceptions.ConnectionError:

        print("❌ ERB server is not running")

        return None


# ============================================================
# DOWNLOAD PDF
# ============================================================

def download_pdf(file_id):

    try:

        response = requests.get(
            f"{SERVER_URL}/download-pdf/{file_id}"
        )

        if response.status_code != 200:

            print("❌ PDF download failed")

            return None

        file_path = DOWNLOAD_DIR / f"{file_id}.pdf"

        with open(file_path, "wb") as file:

            file.write(response.content)

        print("✅ PDF downloaded successfully")

        return file_path

    except requests.exceptions.ConnectionError:

        print("❌ Could not connect to ERB server")

        return None


# ============================================================
# START PRINTING
# ============================================================

def start_printing(order_id):

    try:

        response = requests.post(
            f"{SERVER_URL}/order/{order_id}/start-printing"
        )

        if response.status_code != 200:

            print("❌ Could not start printing")

            print(response.text)

            return False

        print("🖨️ Printing started")

        return True

    except requests.exceptions.ConnectionError:

        print("❌ Could not connect to ERB server")

        return False


# ============================================================
# COMPLETE PRINTING
# ============================================================

def complete_printing(order_id):

    try:

        response = requests.post(
            f"{SERVER_URL}/order/{order_id}/complete-printing"
        )

        if response.status_code != 200:

            print("❌ Could not complete printing")

            print(response.text)

            return False

        print("✅ Printing completed")

        return True

    except requests.exceptions.ConnectionError:

        print("❌ Could not connect to ERB server")

        return False


# ============================================================
# FAIL PRINTING
# ============================================================

def fail_printing(order_id):

    try:

        response = requests.post(
            f"{SERVER_URL}/order/{order_id}/fail-printing"
        )

        if response.status_code != 200:

            print("❌ Could not mark printing as failed")

            print(response.text)

            return False

        print("❌ Printing marked as failed")

        return True

    except requests.exceptions.ConnectionError:

        print("❌ Could not connect to ERB server")

        return False



# ============================================================
# PRINT PDF USING CUPS
# ============================================================

SUPPORTED_PRINTERS = {
    "MF3010",
    "Epson_L3210",
}


def print_pdf(pdf_path, job):
    copies = int(job.get("copies", 1))

    # Use the printer selected for this job.
    # If none is specified, keep using the existing default.
    printer_name = job.get("printer_name") or PRINTER_NAME

    if printer_name not in SUPPORTED_PRINTERS:
        print("Unsupported printer:", printer_name)
        return False

    if copies < 1:
        print("Invalid number of copies:", copies)
        return False

    command = [
        "lp",
        "-d", printer_name,
        "-n", str(copies),
    ]

    # Black-and-white printing
    if job.get("print_type") == "bw":
        command.extend(["-o", "ColorModel=Gray"])

    command.append(str(pdf_path))

    print("\nSending PDF to CUPS...")
    print("Printer:", printer_name)
    print("Copies:", copies)
    print("File:", pdf_path)

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

        if result.returncode != 0:
            print("CUPS printing failed")
            print(result.stderr)
            return False

        print("CUPS accepted print job")
        print(result.stdout.strip())
        return True

    except Exception as error:
        print("Printing error:", error)
        return False



# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(job):

    order_id = job["order_id"]

    file_id = job["file_id"]

    print("")

    print("========================================")

    print("📥 NEW PRINT JOB")

    print("========================================")

    print("Order ID   :", order_id)

    print("Pages      :", job["pages"])

    print("Copies     :", job["copies"])

    print("Print Type :", job["print_type"])

    print("Amount     :", f"₹{job['amount']}")

    print("========================================")

    # --------------------------------------------------------
    # DOWNLOAD PDF
    # --------------------------------------------------------

    pdf_path = download_pdf(file_id)

    if pdf_path is None:

        fail_printing(order_id)

        return

    print("📄 PDF saved to:", pdf_path)

    # --------------------------------------------------------
    # START PRINTING
    # --------------------------------------------------------

    if not start_printing(order_id):

        return

    # --------------------------------------------------------
    # PRINT
    # --------------------------------------------------------

    if SIMULATION_MODE:

        print("")

        print("⚠️ SIMULATION MODE")

        total_pages = job["pages"] * job["copies"]

        for page in range(1, total_pages + 1):

            print(
                f"🖨️ Simulating page "
                f"{page}/{total_pages}"
            )

            time.sleep(1)

        success = True

    else:

        success = print_pdf(
            pdf_path,
            job
        )

    # --------------------------------------------------------
    # UPDATE ORDER STATUS
    # --------------------------------------------------------

    if success:

        complete_printing(order_id)

    else:

        fail_printing(order_id)


# ============================================================
# WORKER LOOP
# ============================================================

def main():

    print("")

    print("🍓 ERB PRINT WORKER")

    print("===================")

    print("Simulation mode:", SIMULATION_MODE)

    print("Server:", SERVER_URL)

    print("Printer:", PRINTER_NAME)

    print("")

    while True:

        print("🔍 Checking print queue...")

        job = get_next_job()

        if job is None:

            print("📭 No print jobs")

            print("")

            time.sleep(5)

            continue

        process_job(job)

        print("")

        print("🔄 Checking for next job...")

        print("")

        time.sleep(2)


# ============================================================
# START WORKER
# ============================================================

if __name__ == "__main__":

    main()
