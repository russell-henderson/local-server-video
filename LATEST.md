# Latest Project Update

**Date:** September 30, 2026

## Local Flask server and network access

The Local Video Server can run directly through Flask on port `8000` without changing the existing Docker setup or application configuration files.

### Start the server

From the project root:

```powershell
.\.venv\Scripts\python.exe main.py --host 0.0.0.0 --port 8000
```

The server binds to all interfaces. Use a colon before the port, not a slash:

- Desktop/LAN: `http://192.168.4.96:8000/`
- Local loopback: `http://127.0.0.1:8000/`
- Tailscale: `http://100.111.201.3:8000/`

### Application changes

- Added `--host` support to `main.py`.
- Added `--port` support to `main.py`.
- Added an optional `--debug` flag for local development.
- Preserved the Flask application factory, route registration, startup tasks, and existing configuration defaults.

### Network and firewall setup

Windows Firewall was configured to allow inbound TCP port `8000` for the Private network profile, covering the local LAN and Tailscale network ranges.

The desktop's Ethernet address is `192.168.4.96`. Tailscale is also active with address `100.111.201.3`; it does not prevent LAN access. Devices using Tailscale can use the Tailscale address, while ordinary LAN devices should use the Ethernet address.

### Verification

- Flask imported successfully from the project virtual environment.
- Application registered 94 routes.
- `GET /ping` returned HTTP 200.
- `GET /` returned HTTP 200.
- Local checks succeeded on both `192.168.4.96:8000` and `100.111.201.3:8000`.
- Successful browser connections were recorded from LAN devices `192.168.4.142` and `192.168.4.105`, including page loads, static assets, video streaming, tags, and view updates.
- The Flask process was stopped after verification; port `8000` is currently not listening.
- A subsequent local run on September 25, 2026 returned HTTP 200 from both `GET /ping` and `GET /`.
- That Flask process was stopped cleanly after verification; port `8000` is free.
- A local run on September 30, 2026 using the documented virtual-environment command returned HTTP 200 from both `GET /ping` and `GET /`.
- The Flask process was stopped cleanly after verification; port `8000` is free.

### Current status

- The local Flask process was stopped on September 30, 2026 after a successful local run.
- Port `8000` is currently free and ready for the documented startup command when needed.

### Intentionally unchanged

- Dockerfile and Docker Compose files were not modified.
- `config.py`, `.env`, and other application configuration files were not modified.
- Existing unrelated working-tree changes were preserved.
