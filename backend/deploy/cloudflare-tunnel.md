# Cloudflare Tunnel setup for uPrint

This guide publishes only the FastAPI API running on the Raspberry Pi. The frontend remains on Cloudflare Pages. SQLite and PDF files remain on the Pi.

## Target

- Local FastAPI origin: `http://127.0.0.1:8000`
- Public API hostname: `https://api.<YOUR_DOMAIN>`
- Customer website: your Cloudflare Pages URL
- Pi worker URL: `http://127.0.0.1:8000` (keep local; do not route the worker through the public hostname)

## Prerequisites

1. A Cloudflare account.
2. For a stable custom hostname, a domain added to Cloudflare with its nameservers delegated to Cloudflare.
3. The Pi has internet access and the uPrint API is running locally.
4. The API health endpoint responds at `curl http://127.0.0.1:8000/health`.

Cloudflare Tunnel uses an outbound connection from the Pi. Do not open inbound router ports or expose CUPS/SSH.

## Recommended: create a remotely-managed tunnel in the dashboard

1. Sign in to the Cloudflare dashboard.
2. Open **Networking → Tunnels** and choose **Create tunnel**.
3. Name it `uprint-pi`.
4. Select the Raspberry Pi operating system and architecture shown by the dashboard.
5. Copy the install/run command displayed for the Pi and run it on the Pi. Treat the token as a secret; do not paste it into GitHub or chat.
6. Wait for the connector to show **Healthy**.
7. In the tunnel, add a **Published application** route:
   - Hostname: `api` and select your Cloudflare-managed domain.
   - Service type: HTTP.
   - Service URL: `http://127.0.0.1:8000`.
8. Save the route.

Cloudflare's dashboard-generated command is authoritative for the account and architecture. Do not use a token from another tunnel.

## Configure uPrint

After the route exists, configure the frontend API base URL in `frontend/config.js`:

```js
window.UPRINT_API_URL = "https://api.YOUR_DOMAIN";
```

Set `CORS_ORIGINS` in the Pi's private `/etc/uprint/uprint.env` to the exact Cloudflare Pages origin, without a trailing slash. Example:

```ini
CORS_ORIGINS=https://YOUR_PROJECT.pages.dev
```

If you later attach a custom website domain to Pages, include that exact origin too (comma-separated). Restart the API after changing its environment:

```bash
sudo systemctl restart uprint-api
```

Keep the worker configured to use the local API:

```ini
UPRINT_SERVER_URL=http://127.0.0.1:8000
```

## Verify

From the Pi:

```bash
curl http://127.0.0.1:8000/health
```

From a device on a different network (for example, phone mobile data), open:

```text
https://api.YOUR_DOMAIN/health
```

Then test a real PDF upload from the deployed Pages website. Confirm the uploaded PDF appears in the Pi's configured `UPLOAD_DIR`, and confirm the order is visible to the local worker.

## Temporary test without a custom domain

Cloudflare Quick Tunnels can provide a temporary `trycloudflare.com` URL for development. It is not a stable production hostname and is not the recommended long-term configuration for the Pages frontend. Use it only for a short connectivity test, and update `UPRINT_API_URL` and CORS accordingly while testing.

## Security checklist

- Keep the tunnel token private and out of source control.
- Keep FastAPI bound to `127.0.0.1`.
- Do not publish CUPS, SSH, the Pi desktop, or other admin services.
- Keep the worker's device token private.
- Set CORS to the exact website origin(s), not `*`.
- Do not put the device token in frontend JavaScript.
- Remember that a public API hostname is internet-accessible; device-only endpoints must continue requiring device authentication.

## Troubleshooting

- **502 / connection refused:** check `sudo systemctl status uprint-api` and `curl http://127.0.0.1:8000/health` on the Pi.
- **Tunnel not healthy:** check the `cloudflared` service status and logs; confirm the Pi has internet access.
- **Browser CORS error:** confirm `CORS_ORIGINS` exactly matches the website origin and restart FastAPI.
- **Upload fails:** inspect FastAPI logs and confirm `UPLOAD_DIR` exists and is writable by the API service user.
