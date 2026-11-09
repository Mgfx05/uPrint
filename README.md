# uPrint — Unified Printing Interface

> **Project handoff and development guide for AI coding assistants (including Gemini and Codex).**
>
> Read this document before changing code. It explains the product goal, current known implementation, target online architecture, development priorities, safety constraints, and how to verify changes.

## 1. Project identity

**Name:** uPrint — Unified Printing Interface  
**Repository:** https://github.com/Mgfx05/uPrint  
**Active development branch:** `redesign/uprint-purple-v1`  
**Primary goal:** Turn the existing local-network PDF printing application into an internet-accessible printing platform.

uPrint allows a customer to open a website, upload a PDF, select printing options, create an order, and track its status. A Raspberry Pi connected to a physical printer receives authorized print jobs through the internet and performs the printing.

### The most important product requirement

The customer device and the Raspberry Pi use **independent internet connections**.

- The customer may use mobile data, home Wi-Fi, office Wi-Fi, or another internet connection.
- The Raspberry Pi may use a separate router, Wi-Fi connection, or mobile hotspot.
- They must not need to be on the same Wi-Fi network or local subnet.
- The customer must never need the Raspberry Pi's local IP address.
- The Raspberry Pi must connect outbound to the cloud service. Do not expose CUPS, SSH, or the Pi directly to the public internet.

This project currently targets **one printing location, one Raspberry Pi 4, and one Epson L3210 printer**. Do not build multi-shop or multi-tenant features unless explicitly requested later.

## 2. Product scope

### Customer experience

1. Open the public uPrint website from any internet connection.
2. Select and upload a PDF.
3. See upload result and detected page count.
4. Choose print settings and quantity.
5. See the calculated price.
6. Create the order and receive an order reference.
7. Track the real order status online.

### Printing location

1. Raspberry Pi connects to the internet independently.
2. A Python print worker authenticates with the cloud backend.
3. The worker checks for available print jobs.
4. It claims one job and downloads its authorized PDF.
5. It submits the PDF to CUPS.
6. CUPS sends the job to the USB-connected Epson L3210.
7. The worker reports progress and the final result to the cloud.

### Explicitly out of scope for the current phase

- Multiple shops or shop accounts.
- Multi-tenant architecture.
- AI assistant or AI document processing.
- Payment gateway integration unless separately approved.
- Replacing the Raspberry Pi, Python worker, or CUPS with a cloud printing service.
- Rewriting the application in React or another frontend framework without approval.

## 3. Current known implementation

The repository has an existing frontend and Python backend. Inspect the actual source code before relying on this summary; code is the final authority.

### Frontend

- Plain HTML, CSS, and JavaScript.
- Main files are expected under `frontend/`:
  - `index.html`
  - `style.css`
  - `app.js`
  - `assets/`
- A purple/violet uPrint visual redesign has been started on the active redesign branch.
- Existing user flows include PDF upload, print options/pricing, order creation, and order tracking.
- Preserve existing DOM IDs, event handlers, request formats, and API integrations unless a change is necessary and documented.

### Backend and printing

Known project technologies and prior implementation include:

- Python and FastAPI.
- PDF page detection using PyPDF.
- Local PDF file storage during the initial implementation.
- An order database and API routes.
- A Python print worker.
- Raspberry Pi 4.
- CUPS printer management.
- Epson L3210 connected over USB.

Previous project work also discussed PostgreSQL, Prisma and Redis, but **do not assume these are currently installed, configured, or used in this repository**. Inspect dependency files, backend code, database models, environment examples, and deployment configuration before proposing or implementing a migration.

### Existing API routes documented by the project

These routes have been used or documented in earlier versions. Verify their current implementation and exact request/response contracts before modifying or relying on them.

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/upload-pdf` | Upload a PDF (multipart field previously named `file`) |
| `GET` | `/calculate-pdf-price` | Calculate print price |
| `POST` | `/create-order` | Create an order |
| `GET` | `/order/{order_id}` | Retrieve order and status |
| `POST` | `/order/{order_id}/queue` | Queue an order |
| `GET` | `/print-queue` | Retrieve queued jobs |
| `POST` | `/order/{order_id}/start-printing` | Mark job as printing |
| `POST` | `/order/{order_id}/complete-printing` | Mark job as completed |
| `POST` | `/order/{order_id}/fail-printing` | Mark job as failed |

Previously documented print options include:
- `print_type`: `bw` or `color`
- `paper_size`: `a4` or `a3`
- `sides`: `single` or `double`
- `orientation`: `portrait` or `landscape`
- `copies`: quantity

Previously documented prices were B&W A4 ₹2/page, B&W A3 ₹4/page, Colour A4 ₹10/page, and Colour A3 ₹20/page. Verify the current pricing implementation before changing or displaying prices. Do not silently alter business rules.

## 4. Target online architecture

The chosen deployment for the current demo is **Cloudflare Pages + Cloudflare Tunnel + FastAPI on the Raspberry Pi**. PDF files and the SQLite database stay on the Pi. No cloud object storage or hosted backend is part of this design.

```text
CUSTOMER DEVICE (any internet connection)
          |
          | HTTPS
          v
CLOUDFLARE PAGES (static uPrint website)
          |
          | HTTPS API requests to api.<your-domain>
          v
CLOUDFLARE EDGE
          |
          | Cloudflare Tunnel (outbound connection from Pi)
          v
RASPBERRY PI 4
  |-- cloudflared
  |-- FastAPI bound to 127.0.0.1:8000
  |-- SQLite database on local disk
  |-- PDF uploads on local disk
  |-- Python print worker
  |-- CUPS
          |
          v
     EPSON L3210 (USB)
```

### Component responsibilities

| Component | Responsibility |
|---|---|
| GitHub | Source control and reviewable changes |
| Cloudflare Pages | Host the public static frontend |
| Cloudflare Tunnel | Securely route public API requests to the Pi without port forwarding |
| FastAPI on Pi | Upload, pricing, order, tracking and device APIs |
| SQLite on Pi | Store demo order records |
| Pi local filesystem | Store uploaded PDF files |
| Python worker | Claim jobs and submit them to CUPS |
| CUPS | Control the USB-connected Epson L3210 |

The customer device and Pi may use completely different internet connections. The Pi initiates the tunnel connection outbound. FastAPI should listen on `127.0.0.1:8000`; do not expose port 8000, CUPS or SSH directly to the internet.

### Current demo scope

- One location, one Raspberry Pi 4, one Epson L3210.
- PDFs stored only on the Pi local disk (default: `backend/uploads`).
- SQLite database stored on the Pi.
- Cloudflare Pages hosts only the static frontend.
- Cloudflare Tunnel publishes the Pi's API hostname.
- No R2, S3, cloud PDF storage, hosted FastAPI backend, Redis, PostgreSQL, multi-shop system, or AI features.
- No payment gateway or payment verification. Orders can be created directly for the demo.

### Public URL arrangement

- Frontend: Cloudflare Pages URL, for example `https://your-uprint.pages.dev`.
- API: a hostname on a domain managed by Cloudflare, for example `https://api.yourdomain.com`.
- Set `window.UPRINT_API_URL` in `frontend/config.js` to the API HTTPS URL.
- Set backend `CORS_ORIGINS` to the exact Pages origin.
- Keep the Pi worker using `http://127.0.0.1:8000`; it does not need to call the public tunnel.

A stable custom API hostname requires a domain added to Cloudflare. A temporary Quick Tunnel can be used for an initial connectivity test, but its generated URL is temporary and should not be used as the production API URL.

## 5. Online print-job lifecycle

The target lifecycle is:

```text
created/pending
      |
      v
queued
      |
      v
claimed (leased to the Pi)
      |
      v
downloading
      |
      v
printing
   /      \\
  v        v
completed  failed
              \\
               v
         needs_attention (when outcome is uncertain)
```

The exact state names must be reconciled with the current implementation before changing database/API contracts.

### Raspberry Pi communication

Start with **authenticated HTTPS polling**. A WebSocket or message broker can be evaluated later if polling proves insufficient.

Expected worker loop:

1. Load device credentials securely from the Pi environment/configuration.
2. Authenticate with the backend.
3. Send periodic heartbeat/health information.
4. Request an available job.
5. Atomically claim the job and receive a lease/claim token.
6. Download the PDF using an authenticated endpoint or short-lived signed URL.
7. Verify the downloaded file and expected metadata/checksum where available.
8. Submit the job to CUPS.
9. Report printing and final status.
10. Continue polling with sensible backoff when no job is available or the network is unavailable.

### Reliability requirements

- A job must not be claimed simultaneously by multiple workers.
- Claims should use leases/expiry so a disconnected Pi does not hold a job forever.
- Job state must be persisted in the database.
- Redis, if used, must not be the only record of queued work.
- API operations should be idempotent where practical.
- A retry must not automatically create a second customer order.
- Worker restarts must recover safely.
- Temporary network failures must not silently delete jobs.
- Store timestamps, attempts, error details and status history.
- Provide a safe operator recovery path for jobs with uncertain outcomes.

**Exactly-once physical printing cannot be guaranteed by network retries alone.** If the printer completes a page but the Pi loses internet before reporting completion, the cloud may not know whether the document printed. Mark such cases as uncertain/needs-attention rather than blindly reprinting and risking duplicates.

## 6. PDF storage and privacy

Local storage is acceptable for local development. For the online deployment, evaluate private object storage such as Cloudflare R2 so the PDF is accessible to the backend and Pi even when the Pi is offline.

Design a storage interface so local filesystem storage and object storage can be selected by configuration without rewriting order logic.

Requirements:

- PDFs must not be publicly listable or accessible through guessable URLs.
- Enforce upload size limits and validate actual PDF content, not only file extensions.
- Generate unique server-side document identifiers and safe filenames.
- Authorize every document download.
- Use short-lived signed URLs or authenticated download endpoints.
- Keep temporary Pi copies in a controlled directory and remove them according to policy.
- Define document retention and automatic deletion.
- Do not log PDF contents, credentials, signed URLs, or unnecessary personal data.
- Ensure an order cannot access another order's document.

Do not move to R2 until the current local upload/download flow is understood and tested.

## 7. Security requirements

- HTTPS for all public and device communication.
- No backend secrets or device credentials in frontend JavaScript.
- Unique device credential for the Raspberry Pi, stored outside source control.
- Ability to revoke and rotate device credentials.
- Do not expose CUPS, SSH, or Pi administration ports publicly.
- Validate all user input and uploaded files on the backend.
- Apply upload limits and appropriate rate limits.
- Restrict CORS to known frontend origins when frontend and backend use separate origins.
- Protect order tracking from easy enumeration; use sufficiently unguessable references or an additional verification mechanism.
- Use least-privilege credentials for database, storage and device operations.
- Keep secrets in deployment environment variables or a secure secret manager.
- Add audit logs for sensitive job and device actions.

## 8. Frontend design requirements

Continue the existing uPrint redesign:

- Purple/violet brand identity.
- Responsive navigation and promotional hero section.
- PDF drag-and-drop and browse upload.
- Clear print options and price calculation.
- Order confirmation and reference ID.
- Real order tracking based on backend status.
- Accessible Upload → Print → Collect workflow animation.
- Mobile and desktop support.

The workflow animation is explanatory UI only. It must not claim that a customer's job is printing or completed unless the backend reports that state.

Keep the current plain HTML/CSS/JavaScript architecture unless explicitly approved to change it.

## 9. Development workflow and repository safety

**Active branch:** `redesign/uprint-purple-v1`

- Make development changes on the active redesign branch.
- Do not commit redesign work directly to `main`.
- Do not merge to `main` without explicit approval.
- Preserve the existing ZIP/extracted backup.
- Inspect `git status` before modifying or overwriting files.
- Do not discard uncommitted user changes.
- Create meaningful commits/checkpoints after stable milestones.
- Update this README and `docs/VERSION_HISTORY.md` when architecture or milestones change.
- Never commit secrets, API keys, credentials, customer PDFs, database files, or local environment files.
- Use an example environment file with placeholder values only.

Suggested commit messages:
- `docs: clarify online architecture`
- `feat: add cloud device polling API`
- `feat: add persistent print job claims`
- `fix: recover expired print job leases`
- `test: cover worker reconnect behaviour`

## 10. Instructions for Gemini / Codex / other AI coding assistants

Before writing code:

1. Read this README completely.
2. Inspect the repository tree and current Git branch/status.
3. Inspect frontend files, FastAPI entry point, routers, database models, worker, CUPS configuration, dependency files, and environment configuration.
4. Identify which statements in this README match code and which describe future requirements.
5. Produce a short implementation plan that names exact files and API contracts to change.
6. Ask before destructive migrations, framework changes, or changes to printer/business rules.

While coding:

- Make small, reviewable changes.
- Preserve existing working upload, pricing, order and printing behaviour.
- Do not invent endpoints, schemas, environment variables, or dependencies without implementing and documenting them.
- Do not assume PostgreSQL, Prisma, Redis, R2 or cloud hosting is already configured.
- Keep local development usable.
- Add tests for new API and worker behaviour.
- Never fake a successful print status.
- Keep secrets out of source code.
- Do not implement multi-shop or AI features in this phase.

After each milestone, report:
- What was inspected.
- Files changed.
- API/schema changes.
- Dependencies or environment variables added.
- Tests run and their results.
- Known risks or incomplete work.
- Git commit/checkpoint created.

## 11. Implementation roadmap

### Phase 0 — Repository audit
- [ ] Confirm active branch and clean/dirty Git state.
- [ ] Map actual frontend and backend files.
- [ ] Confirm current database and schema.
- [ ] Confirm actual upload storage path and lifecycle.
- [ ] Confirm print worker behaviour and CUPS printer configuration.
- [ ] Record current API request/response contracts.
- [ ] Identify existing tests and run baseline tests.

### Phase 1 — Stabilize current application
- [ ] Finish and test frontend redesign.
- [ ] Verify PDF upload and validation.
- [ ] Verify pricing and order creation.
- [ ] Verify order tracking.
- [ ] Verify local Pi-to-printer flow.
- [ ] Document known limitations.

### Phase 2 — Cloud foundation
- [ ] Select Cloudflare Pages project and connect GitHub.
- [ ] Select a Python-compatible FastAPI host.
- [ ] Configure domain and HTTPS.
- [ ] Configure persistent database.
- [ ] Configure backend secrets and environment variables.
- [ ] Test public health endpoint.

### Phase 3 — Pi-local document flow
- [ ] Confirm secure upload validation and file-size limits.
- [ ] Confirm PDFs are saved only on the Pi.
- [ ] Confirm authorized worker download from the Pi API.
- [ ] Define local PDF retention and cleanup.
- [ ] Test uploads from a device on a separate network.

### Phase 4 — Cloud job and device APIs
- [ ] Design persistent job schema/state transitions.
- [ ] Implement device registration/authentication.
- [ ] Implement heartbeat.
- [ ] Implement atomic job claiming and lease expiry.
- [ ] Implement job download authorization.
- [ ] Implement status reporting and idempotency.
- [ ] Add tests for concurrent claims and retries.

### Phase 5 — Raspberry Pi online worker
- [ ] Configure independent Pi internet access.
- [ ] Store device credentials securely.
- [ ] Implement HTTPS polling and backoff.
- [ ] Implement claim/download/validation.
- [ ] Integrate with existing CUPS printing.
- [ ] Report actual printing outcomes.
- [ ] Recover safely after reboot/network loss.

### Phase 6 — End-to-end acceptance test
- [ ] Customer device uses mobile data or another independent network.
- [ ] Raspberry Pi uses a different internet connection.
- [ ] Customer uploads a PDF.
- [ ] Backend creates and persists an order.
- [ ] Pi discovers and claims the job.
- [ ] Pi downloads the correct PDF.
- [ ] Epson L3210 prints the document.
- [ ] Backend records the real result.
- [ ] Customer sees updated order status.
- [ ] Disconnect/reconnect tests do not silently lose or duplicate jobs.

## 12. Definition of done

The online conversion is complete only when a customer and Raspberry Pi operating on **separate internet connections** can complete the full upload → order → cloud queue → Pi download → CUPS print → status update flow.

The system must also handle temporary network interruptions safely, protect private PDFs and device credentials, and preserve the existing local development workflow.

---

**Guiding principle:** Make the existing uPrint system work online. Do not rebuild it unnecessarily. Keep one printing location and one Raspberry Pi in scope, preserve working hardware integration, and introduce cloud components only when they solve a demonstrated requirement.
Preview deployments are configured through Cloudflare Wrangler.
