# Raspberry Pi deployment

This folder contains templates for running the uPrint FastAPI service on the Pi.

## Assumptions

- Raspberry Pi OS / Debian with systemd.
- Repository cloned to `/home/<PI_USER>/uPrint`.
- Python virtual environment at `/home/<PI_USER>/uPrint/.venv`.
- API listens only on `127.0.0.1:8000`; Cloudflare Tunnel will proxy to this local address.
- SQLite database and uploaded PDFs remain on the Pi.

## One-time setup

Replace `<PI_USER>` with the actual Linux username and adjust the repository path if needed.

```bash
cd /home/<PI_USER>/uPrint
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt
sudo mkdir -p /etc/uprint
sudo cp backend/deploy/uprint.env.example /etc/uprint/uprint.env
sudo chmod 600 /etc/uprint/uprint.env
```

Edit `/etc/uprint/uprint.env`: set the actual absolute paths, generate a strong DEVICE_TOKEN, and set CORS_ORIGINS to the deployed Pages origin. Never commit the real environment file or token.

Copy `backend/deploy/uprint-api.service.example` to `/etc/systemd/system/uprint-api.service`, replace the username and repository path in it, then run:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now uprint-api
sudo systemctl status uprint-api
curl http://127.0.0.1:8000/health
```

Logs:

```bash
sudo journalctl -u uprint-api -f
```

## Before enabling the public tunnel

1. Confirm the local health endpoint works.
2. Confirm the frontend loads from the expected repository path.
3. Confirm the upload directory is writable by the service user.
4. Configure Cloudflare Tunnel to proxy to `http://127.0.0.1:8000`.
5. Keep CUPS and SSH private; do not create public port-forwarding rules.

The service template intentionally uses placeholders. It is not ready to install until paths and the Linux username are replaced.
