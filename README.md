# uPrint — Unified Printing Interface

uPrint is a streamlined, self-service document-printing platform. Upload a PDF, choose your print settings, create an order, and follow its progress from queue to collection — all from one responsive web interface.

The product is designed for a local print desk or kiosk setup, with a FastAPI backend, local PDF storage, an SQLite order store, and a print worker that can run on a Raspberry Pi.

## What uPrint does

- Upload and validate PDF documents (up to 50 MB in the browser).
- Detect document page counts automatically.
- Choose B&W or colour printing, copies, A4/A3 paper, sides, and orientation.
- Calculate the total price live before an order is created.
- Create a print order and display its reference ID.
- Track the live order status using the backend as the source of truth.
- Explain the Upload → Print → Collect process with an accessible, reduced-motion-friendly visual workflow.

## Experience and branding

The frontend uses the uPrint purple/violet visual identity: a promotional hero banner, clear option cards, responsive navigation, file-upload feedback, an order confirmation view, live tracking, and a branded footer. It is built with plain HTML, CSS, and JavaScript — no frontend framework or animation library is required.

## Architecture

```text
Browser (uPrint frontend)
        │ upload, configure, create and track orders
        ▼
FastAPI application
        ├── Local PDF storage
        ├── SQLite order database
        └── Print queue
                  │
                  ▼
        Raspberry Pi print worker → CUPS → printer
```

The frontend and API are served from the same FastAPI process, avoiding cross-origin configuration for the normal local deployment.

## Project layout

```text
uPrint/
├── backend/
│   ├── main.py                 # FastAPI application and frontend mount
│   ├── routes/                 # Upload, pricing, health, and order APIs
│   ├── models/                 # SQLite database and order model
│   ├── services/               # Pricing rules
│   └── print_worker.py         # Print-queue worker
├── frontend/
│   ├── index.html              # uPrint interface
│   ├── style.css               # Responsive uPrint design system
│   ├── app.js                  # Upload, pricing, order, and tracking flows
│   └── assets/                 # uPrint logo assets
└── docs/
    └── VERSION_HISTORY.md      # Redesign checkpoints
```

## Run locally

### Prerequisites

- Python 3.10 or newer
- `pip`

### Setup

```bash
cd backend
python -m venv venv
```

Activate the environment:

```bash
# Windows PowerShell
.\\venv\\Scripts\\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

Install the backend dependencies:

```bash
pip install fastapi "uvicorn[standard]" python-multipart pypdf sqlalchemy requests
```

Start the application:

```bash
uvicorn main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). The FastAPI application serves both the API and the uPrint frontend.

## Printing prices

| Print type | A4 rate | A3 rate |
|---|---:|---:|
| B&W | ₹2 per page | ₹4 per page |
| Colour | ₹10 per page | ₹20 per page |

The total is calculated as `pages × copies × price per page`. The interface accepts from 1 to 50 copies.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Confirm that the service is available. |
| `POST` | `/upload-pdf` | Upload a PDF as multipart form field `file`. |
| `GET` | `/calculate-pdf-price` | Calculate a document price from its `file_id` and options. |
| `POST` | `/create-order` | Create an order from an uploaded document. |
| `GET` | `/order/{order_id}` | Retrieve an order and its actual print status. |
| `POST` | `/order/{order_id}/queue` | Queue a pending order. |
| `GET` | `/print-queue` | List queued print jobs. |
| `POST` | `/order/{order_id}/start-printing` | Mark a queued order as printing. |
| `POST` | `/order/{order_id}/complete-printing` | Mark a printing order as completed. |
| `POST` | `/order/{order_id}/fail-printing` | Mark a printing order as failed. |

`/create-order` and `/calculate-pdf-price` support these query parameters: `file_id`, `copies`, `print_type` (`bw` or `color`), `paper_size` (`a4` or `a3`), `sides` (`single` or `double`), and `orientation` (`portrait` or `landscape`).

## Order lifecycle

```text
pending → queued → printing → completed
                     └──────→ failed
```

uPrint’s workflow animation is informational. The order tracking card always displays the real `print_status` returned by the API and never marks an order as printed or collected on its own.

## Print worker and printer integration

The print worker polls the queue, downloads the relevant PDF, updates order state, and sends jobs to the configured printer. It is intended for Raspberry Pi deployments with CUPS and supports the Epson L3210 configuration used by this project. Keep the worker and printer configuration aligned with the local deployment before enabling live printing.

## Current scope

- Payments and authentication are not implemented.
- PDFs and the SQLite database are stored locally.
- The frontend preserves the existing backend routes and request/response formats.

## Development branch

Frontend redesign work is maintained on `redesign/uprint-purple-v1`. See [docs/VERSION_HISTORY.md](docs/VERSION_HISTORY.md) for recovery and checkpoint information.
