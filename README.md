# ERB — Easy Print & Collect

> A self-service PDF printing kiosk: upload a PDF, choose print options, place an order, and collect your prints. No login, no app install.

## Status

🚧 **Work in progress.** The upload → order → queue → print pipeline is functional and has been tested end-to-end, including with a simulated Raspberry Pi print worker.

**Payment is not implemented yet.** Orders are currently created with `payment_status: "pending"`; payment collection is a planned next phase (see [Roadmap](#roadmap)).

## Table of contents

- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Setup](#setup)
- [Running the project](#running-the-project)
- [API reference](#api-reference)
- [Order status lifecycle](#order-status-lifecycle)
- [Pricing](#pricing)
- [Frontend notes](#frontend-notes)
- [Quick manual test (curl)](#quick-manual-test-curl)
- [Raspberry Pi print worker](#raspberry-pi-print-worker)
- [Roadmap](#roadmap)
- [Known limitations](#known-limitations)

## How it works

**System architecture**

```
Frontend (browser)
      │  upload PDF, choose options, place order
      ▼
FastAPI Backend  ──────────────►  PDF Storage (backend/uploads/)
      │
      ▼
SQLite Database (Orders)
      │  order picked up from queue
      ▼
Raspberry Pi Print Worker
      │
      ▼
Physical Printer
```

**User flow**

```
Open website
   → Select PDF
   → Upload
   → See file name + page count
   → Choose B&W / Color
   → Choose number of copies
   → See live price
   → Click Place Order
   → Order created in database (payment_status: pending)
   → [Payment — added later]
   → Order queued
   → Picked up by Raspberry Pi print worker
   → Printed
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML / CSS / JavaScript |
| Backend | FastAPI (Python) |
| Database | SQLite |
| File storage | Local filesystem (`backend/uploads/`) |
| Print worker | Python script on Raspberry Pi |

## Project structure

```
~
├── backend/
│   ├── main.py              # FastAPI app, router registration, static file mount
│   ├── routes/
│   │   ├── health.py        # Health check endpoint
│   │   ├── upload.py        # PDF upload handling
│   │   ├── pricing.py       # Pricing logic
│   │   └── orders.py        # Order lifecycle endpoints
│   ├── models/
│   │   ├── database.py      # SQLite connection / schema
│   │   └── order.py         # Order data model
│   └── uploads/              # Uploaded PDFs are stored here
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── raspberry-pi/            # Print worker script(s)
└── docs/
```

## Setup

**Prerequisites:** Python 3.10+, pip

1. **Clone and enter the project**
   ```bash
   git clone <your-repo-url>
   cd erb
   ```

2. **Create a virtual environment and install backend dependencies**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install fastapi "uvicorn[standard]" python-multipart pypdf
   ```
   > Adjust this list to match your actual `requirements.txt` if one exists in the repo.

## Running the project

```bash
cd backend
uvicorn main:app --reload
```

Backend **and** frontend are both served from:
```
http://127.0.0.1:8000
```

### Why a single server

Earlier versions served the frontend separately via a dev server (e.g. VS Code Live Server) on port `5500`. That caused two problems: cross-origin requests needing CORS, and the dev server's file watcher triggering full-page reloads whenever a new PDF was saved into `backend/uploads/`, which reset in-progress UI state mid-order. The fix was to serve the frontend directly from FastAPI:

```python
# at the very end of backend/main.py, after all app.include_router(...) calls
from fastapi.staticfiles import StaticFiles

app.mount("/", StaticFiles(directory="../frontend", html=True), name="frontend")
```

Everything now runs from one origin, so no CORS configuration or second dev server is required. If you ever do split the frontend onto a different origin/port again, add `CORSMiddleware` in `main.py` and explicitly allow that origin.

## API reference

Base URL: `http://127.0.0.1:8000`

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Basic health check |

### Upload

| Method | Path | Description |
|---|---|---|
| POST | `/upload-pdf` | Upload a PDF (`multipart/form-data`, field name `file`). Returns a `file_id`, page count, and file size. |

**Example response**
```json
{
  "message": "PDF uploaded successfully",
  "file_id": "4aa9bf3b-0dba-4eb2-a9b5-d80ae3e3a751",
  "filename": "3rd sem result.pdf",
  "pages": 2,
  "file_size_bytes": 512275
}
```

### Orders

| Method | Path | Description |
|---|---|---|
| POST | `/create-order` | Create an order from an uploaded file. Query params: `file_id`, `copies`, `print_type` (`bw` or `color`). |
| GET | `/order/{order_id}` | Fetch a single order by ID. |
| POST | `/order/{order_id}/queue` | Move an order into the print queue. |
| GET | `/print-queue` | List all queued orders. |
| POST | `/order/{order_id}/start-printing` | Mark an order as printing (called by the print worker). |
| POST | `/order/{order_id}/complete-printing` | Mark an order as completed. |
| POST | `/order/{order_id}/fail-printing` | Mark an order as failed. Only valid while an order is `printing` — see below. |

**Example order**
```json
{
  "message": "Order created successfully",
  "order_id": "ERB-C8C0F4DC",
  "file_id": "4aa9bf3b-0dba-4eb2-a9b5-d80ae3e3a751",
  "pages": 2,
  "copies": 1,
  "print_type": "bw",
  "amount": 4,
  "payment_status": "pending",
  "print_status": "pending"
}
```

## Order status lifecycle

```
pending → queued → printing → completed
                        │
                        └──→ failed
```

An order can only be marked `failed` while it is `printing`. Attempting to fail an already-`completed` order correctly returns a `400` — this is expected validation, not a bug:
```json
{ "detail": "Order cannot be marked as failed. Current status: completed" }
```

## Pricing

| Type | Rate |
|---|---|
| B&W | ₹2 / page |
| Color | ₹10 / page |

Price is calculated client-side in `app.js`: `pages × copies × price_per_page`, and recalculated live whenever the print type or copy count changes.

## Frontend notes

- `app.js` drives the full flow: file select → upload → show options → calculate price → place order → show result.
- All interactive buttons (`orderBtn`, `minusBtn`, `plusBtn`) are `type="button"`, which prevents accidental form submission or page reload.
- Errors surface in `#errorMessage` and are only cleared on the next user action (new file, retrying the order) — never on a timer.
- `optionsCard` and `orderCard` are toggled via a shared `.hidden { display: none }` class in `style.css`.

## Quick manual test (curl)

```bash
# 1. Upload a PDF
curl -X POST http://127.0.0.1:8000/upload-pdf \
  -F "file=@/path/to/your/file.pdf"

# 2. Create an order (use the file_id returned above)
curl -X POST "http://127.0.0.1:8000/create-order?file_id=<FILE_ID>&copies=1&print_type=bw"

# 3. Queue the order (use the order_id returned above)
curl -X POST "http://127.0.0.1:8000/order/<ORDER_ID>/queue"

# 4. Check the queue
curl http://127.0.0.1:8000/print-queue
```

## Raspberry Pi print worker

The worker (in `raspberry-pi/`) polls `/print-queue`, downloads the PDF for each queued order, and prints it — currently running in **simulation mode**, which logs each page instead of sending it to a real printer:

```
ERB PRINT WORKER
Simulation mode: True

New print job received
PDF downloaded successfully
Printing started
Simulating page 1/2
Simulating page 2/2
Simulation finished
Printing completed
```

On success it calls `/order/{order_id}/complete-printing`; on failure it should call `/order/{order_id}/fail-printing` while the order is still `printing`.

## Roadmap

- [ ] Payment integration (timing relative to order placement TBD)
- [ ] Raspberry Pi print worker: replace simulation mode with real printer calls
- [ ] Admin dashboard for queue monitoring
- [ ] Order history / lookup
- [ ] Receipt or pickup/collection code

## Known limitations

- No authentication — anyone with access to the URL can upload and place orders.
- No payment gateway yet; every order is created with `payment_status: "pending"`.
- Print worker currently runs in simulation mode only, not connected to a physical printer.
- License: not yet decided.
