# Latest Project Update

**Date:** October 12, 2026

## Local Flask server and network access

The Local Video Server can run directly through Flask on port `8000` without changing the existing Docker setup or application configuration files.

### Start the server

From the project root:

```powershell
.\dev.ps1 dev
```

The server binds to all interfaces. Use a colon before the port, not a slash:

- Desktop/LAN: `http://192.168.4.96:8000/`
- Local loopback: `http://127.0.0.1:8000/`
- Tailscale: `http://100.111.201.3:8000/`

### Application changes

- No changes made to main.py or configuration files during this session.
- Used existing dev.ps1 script for development server startup.

### Network and firewall setup

Windows Firewall was configured to allow inbound TCP port `8000` for the Private network profile, covering the local LAN and Tailscale network ranges.

The desktop's Ethernet address is `192.168.4.96`. Tailscale is also active with address `100.111.201.3`; it does not prevent LAN access. Devices using Tailscale can use the Tailscale address, while ordinary LAN devices should use the Ethernet address.

### Verification

- Flask imported successfully from the project environment.
- Application registered routes successfully.
- `GET /ping` returned HTTP 200.
- `GET /` returned HTTP 200.
- Local checks succeeded on both `192.168.4.96:8000` and `100.111.201.3:8000`.
- Successful browser connections were recorded from LAN devices.
- The Flask process was stopped after verification; port `8000` is currently not listening.

### Current status

- The local Flask process was stopped on October 12, 2026 after a successful local run.
- Port `8000` is currently free and ready for the documented startup command when needed.

### Intentionally unchanged

- Dockerfile and Docker Compose files were not modified.
- `config.py`, `.env`, and other application configuration files were not modified.
- Existing unrelated working-tree changes were preserved.
