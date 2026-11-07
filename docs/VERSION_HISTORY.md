# uPrint version history

This file records safe frontend redesign checkpoints. The production baseline remains on `main`.

## Recovery rules

- Never develop directly on `main`.
- Keep the redesign on `redesign/uprint-purple-v1`.
- Each meaningful checkpoint is committed separately.
- Before a risky change, fetch the latest branch files and preserve the current checkpoint.
- To recover, check out the desired commit or reset a local working copy to that commit. Do not force-push over `main`.

## Checkpoints

| Version | Branch | Scope | Status |
|---|---|---|---|
| Baseline | `main` | Original ERB frontend and existing API integration | Preserved |
| V1.0 | `redesign/uprint-purple-v1` | uPrint identity, UΠ brand language, purple/violet theme, logo asset, existing frontend structure and interactions retained | In progress |

## V1.0 files touched

- `frontend/index.html` — uPrint page title, metadata, brand navigation, hero copy, footer and order-ID hint.
- `frontend/style.css` — uPrint purple visual tokens and brand styling layered over existing component styles.
- `frontend/assets/uprint-logo.svg` — reusable vector logo asset.

## Not changed in V1.0

- `frontend/app.js`
- FastAPI backend and API routes
- SQLite database and local PDF storage
- Raspberry Pi print worker and CUPS configuration

## Verification still required

Run the application locally and test PDF upload, pricing, order creation, order tracking, mobile navigation and responsive layouts before merging to `main`.
