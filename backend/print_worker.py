import requests
import time
from pathlib import Path


# ============================================================
# ERB PRINT WORKER
# ============================================================

SERVER_URL = "http://127.0.0.1:8000"

DOWNLOAD_DIR = Path("worker_downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

SIMULATION_MODE = True


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
# SIMULATE PRINTING
# ============================================================

def simulate_print(job):

    print("")
    print("========================================")
    print("       ERB PRINT SIMULATION")
    print("========================================")

    print(f"Order ID   : {job['order_id']}")
    print(f"Pages      : {job['pages']}")
    print(f"Copies     : {job['copies']}")
    print(f"Print Type : {job['print_type']}")
    print(f"Amount     : ₹{job['amount']}")

    print("")

    total_pages = job["pages"] * job["copies"]

    for page in range(1, total_pages + 1):

        print(
            f"🖨️ Simulating page "
            f"{page}/{total_pages}"
        )

        time.sleep(1)

    print("")
    print("✅ Simulation finished")
    print("========================================")


# ============================================================
# PROCESS ONE JOB
# ============================================================

def process_job(job):

    order_id = job["order_id"]
    file_id = job["file_id"]

    print("")
    print("📥 New print job received")
    print(f"Order: {order_id}")

    # Download PDF
    pdf_path = download_pdf(file_id)

    if pdf_path is None:
        return

    print(f"📄 PDF saved to: {pdf_path}")

    # Start printing
    if not start_printing(order_id):
        return

    # Simulate printing
    if SIMULATION_MODE:

        simulate_print(job)

    # Mark completed
    complete_printing(order_id)


# ============================================================
# WORKER LOOP
# ============================================================

def main():

    print("")
    print("🍓 ERB PRINT WORKER")
    print("===================")
    print("Simulation mode:", SIMULATION_MODE)
    print("Server:", SERVER_URL)
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