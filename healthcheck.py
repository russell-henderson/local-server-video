#!/usr/bin/env python3
"""
Local Video Server — Comprehensive Health Check
- Run as CLI:      python healthcheck.py
- FastAPI mount:   from healthcheck import router; app.include_router(router)

Exit codes:
 0 OK, 1 WARN (degraded), 2 FAIL (critical)
"""

from __future__ import annotations
import os, sys, json, time, shutil, socket, subprocess, ctypes, platform
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional

# ---------- Defaults (override via env or CLI flags later if you like) ----------
CFG = {
    "APP_HOST": os.getenv("LVS_HOST", "127.0.0.1"),
    "APP_PORT": int(os.getenv("LVS_PORT", "8080")),
    "DB_PATH": Path(os.getenv("LVS_DB_PATH", r"V:\video-server\app.db")).as_posix(),
    "VIDEOS_DIR": Path(
        os.getenv("LVS_VIDEOS_DIR", r"V:\local-video-server\videos")
    ).as_posix(),
    "CACHE_DIR": Path(os.getenv("LVS_CACHE_DIR", r"V:\video-server\cache")).as_posix(),
    "CACHE_CAP_BYTES": int(
        os.getenv("LVS_CACHE_CAP_BYTES", str(50 * 1024**3))
    ),  # 50 GB
    "BACKUP_DIR": Path(
        os.getenv("LVS_BACKUP_DIR", r"E:\media-server-backups")
    ).as_posix(),
    "BACKUP_FRESH_HOURS": int(os.getenv("LVS_BACKUP_FRESH_HOURS", "36")),
    "MEILI_HOST": os.getenv("MEILI_HOST", "127.0.0.1"),
    "MEILI_PORT": int(os.getenv("MEILI_PORT", "7700")),
    "MEILI_KEY": os.getenv("MEILI_MASTER_KEY", ""),
    "INDEX_NAME": os.getenv("LVS_INDEX", "media"),
    "ALLOWLIST_FILE": Path(
        os.getenv("LVS_ALLOWLIST_FILE", r"V:\video-server\allowlist.txt")
    ).as_posix(),
    "QUIET_HOURS_START": int(os.getenv("LVS_QUIET_START", "1")),  # 1 AM
    "QUIET_HOURS_END": int(os.getenv("LVS_QUIET_END", "6")),  # 6 AM
    "SIDECAR_EXT": ".json",
    "FFMPEG_BIN": os.getenv("FFMPEG_BIN", "ffmpeg"),
    "FFPROBE_BIN": os.getenv("FFPROBE_BIN", "ffprobe"),
    "SSL_CERT": Path(
        os.getenv("LVS_SSL_CERT", r"V:\video-server\certs\server.crt")
    ).as_posix(),
    "SSL_KEY": Path(
        os.getenv("LVS_SSL_KEY", r"V:\video-server\certs\server.key")
    ).as_posix(),
    "MAX_AI_JOBS": int(os.getenv("LVS_MAX_AI_JOBS", "2")),
    "MAX_TRANSCODE_BITRATE": int(
        os.getenv("LVS_MAX_TRANSCODE_BITRATE", "15000000")
    ),  # 15 Mbps
    "WAL_REQUIRED": True,  # per spec use WAL mode
}


# ---------- Helpers ----------
def _ok(msg, **extra):
    return {"status": "ok", "msg": msg, **extra}


def _warn(msg, **extra):
    return {"status": "warn", "msg": msg, **extra}


def _fail(msg, **extra):
    return {"status": "fail", "msg": msg, **extra}


def _bytes_fmt(n: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore
    return f"{n:.1f} PB"


def _drive_free_bytes(path: str) -> int:
    try:
        return shutil.disk_usage(path).free
    except Exception:
        return -1


def _check_port_open(host: str, port: int, timeout=0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False


def _run(cmd: List[str], timeout: int = 6) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except Exception as e:
        return 127, "", str(e)


def _recent_file_in(dir_path: str, within_hours: int) -> Optional[Path]:
    p = Path(dir_path)
    if not p.exists():
        return None
    fresh_after = time.time() - within_hours * 3600
    newest = None
    newest_ts = 0
    for f in p.rglob("*"):
        if f.is_file():
            ts = f.stat().st_mtime
            freshest = newest_ts
            if ts > freshest:
                newest = f
                newest_ts = int(ts)
    if newest and newest_ts >= fresh_after:
        return newest
    return None


def _sum_dir_bytes(path: str, limit_files: Optional[int] = None) -> int:
    total = 0
    count = 0
    for root, _, files in os.walk(path):
        for name in files:
            try:
                total += Path(root, name).stat().st_size
            except OSError:
                pass
            count += 1
            if limit_files and count >= limit_files:
                return total
    return total


def _is_admin_windows() -> bool:
    if platform.system() != "Windows":
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


# ---------- Checks ----------
def check_app_port(cfg) -> Dict[str, Any]:
    port_ok = _check_port_open(cfg["APP_HOST"], cfg["APP_PORT"])
    return (
        _ok("App HTTP port open")
        if port_ok
        else _warn(
            "App port closed (server not running?)",
            host=cfg["APP_HOST"],
            port=cfg["APP_PORT"],
        )
    )


def check_sqlite(cfg) -> Dict[str, Any]:
    import sqlite3

    db_path = cfg["DB_PATH"]
    p = Path(db_path)
    if not p.exists():
        return _fail("SQLite DB not found", path=db_path)

    try:
        con = sqlite3.connect(f"file:{db_path}?mode=rw", uri=True, timeout=3)
        cur = con.cursor()

        wal_mode = cur.execute("PRAGMA journal_mode;").fetchone()[0]
        wal_ok = (wal_mode.lower() == "wal") if cfg["WAL_REQUIRED"] else True

        integrity = cur.execute("PRAGMA integrity_check;").fetchone()[0]
        integrity_ok = integrity.lower() == "ok"

        # optional tables
        tables = [
            r[0]
            for r in cur.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        sample_counts = {}
        for t in ["media", "sidecars", "albums", "tags"]:
            if t in tables:
                try:
                    c = cur.execute(f"SELECT COUNT(1) FROM {t};").fetchone()[0]
                    sample_counts[t] = c
                except Exception:
                    pass

        con.close()

        status = (
            "ok" if (wal_ok and integrity_ok) else ("warn" if integrity_ok else "fail")
        )
        msg = "SQLite healthy"
        if not wal_ok:
            msg = "SQLite OK but WAL disabled"
        if not integrity_ok:
            msg = "SQLite integrity_check failed"

        return {
            "status": status,
            "msg": msg,
            "path": db_path,
            "wal_mode": wal_mode,
            "integrity_check": integrity,
            "tables": tables,
            "counts": sample_counts,
            "size_bytes": p.stat().st_size,
            "free_bytes_on_drive": _drive_free_bytes(str(p.drive or p.parent)),
        }
    except Exception as e:
        return _fail("SQLite open/PRAGMA failed", error=str(e), path=db_path)


def check_meilisearch(cfg) -> Dict[str, Any]:
    # TCP first
    if not _check_port_open(cfg["MEILI_HOST"], cfg["MEILI_PORT"]):
        return _warn(
            "Meilisearch port closed", host=cfg["MEILI_HOST"], port=cfg["MEILI_PORT"]
        )

    # HTTP probe without external deps
    import http.client

    try:
        conn = http.client.HTTPConnection(
            cfg["MEILI_HOST"], cfg["MEILI_PORT"], timeout=2
        )
        headers = {}
        if cfg["MEILI_KEY"]:
            headers["Authorization"] = f"Bearer {cfg['MEILI_KEY']}"
        conn.request("GET", "/health", headers=headers)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8", "ignore")
        healthy = (resp.status == 200) and (
            "available" in body.lower() or "ok" in body.lower()
        )

        # try an index stats call
        conn.request("GET", f"/indexes/{cfg['INDEX_NAME']}/stats", headers=headers)
        stats_resp = conn.getresponse()
        stats_body = stats_resp.read().decode("utf-8", "ignore")
        return {
            "status": "ok" if healthy else "warn",
            "msg": (
                "Meilisearch reachable"
                if healthy
                else "Meilisearch reachable but not healthy"
            ),
            "health_body": body[:300],
            "index_stats_sample": stats_body[:500],
        }
    except Exception as e:
        return _fail("Meilisearch HTTP probe failed", error=str(e))


def check_cache(cfg) -> Dict[str, Any]:
    cdir = cfg["CACHE_DIR"]
    p = Path(cdir)
    if not p.exists():
        return _warn("Cache directory missing", path=cdir)

    used = _sum_dir_bytes(cdir)
    cap = cfg["CACHE_CAP_BYTES"]
    ratio = used / cap if cap > 0 else 0
    status = "ok" if ratio <= 0.85 else ("warn" if ratio <= 1.0 else "fail")
    return {
        "status": status,
        "msg": (
            "Cache usage OK"
            if status == "ok"
            else ("Cache near/full" if status == "warn" else "Cache exceeds cap")
        ),
        "used_bytes": used,
        "cap_bytes": cap,
        "usage_pct": round(100 * ratio, 1),
    }


def check_videos_and_sidecars(cfg) -> Dict[str, Any]:
    vdir = Path(cfg["VIDEOS_DIR"])
    if not vdir.exists():
        return _fail("Videos directory not found", path=str(vdir))
    # quick scan
    videos = []
    sidecar_mismatches = []
    checked = 0
    for f in vdir.rglob("*"):
        if f.suffix.lower() in {".mp4", ".mkv", ".mov", ".webm"}:
            checked += 1
            videos.append(f)
            sc = f.with_suffix(cfg["SIDECAR_EXT"])
            if not sc.exists():
                sidecar_mismatches.append(str(f.relative_to(vdir)))
            if checked >= 200:  # cap for speed
                break
    return {
        "status": "ok" if len(sidecar_mismatches) == 0 else "warn",
        "msg": (
            "Videos/sidecars OK"
            if len(sidecar_mismatches) == 0
            else "Missing sidecars detected"
        ),
        "sample_checked": checked,
        "missing_sidecars": sidecar_mismatches[:30],
    }


def check_ffmpeg(cfg) -> Dict[str, Any]:
    rc_v, out_v, err_v = _run([cfg["FFMPEG_BIN"], "-version"])
    if rc_v != 0:
        return _fail("ffmpeg not available", error=err_v or out_v)

    rc_e, out_e, _ = _run([cfg["FFMPEG_BIN"], "-encoders"])
    nvenc = "hevc_nvenc" in out_e or "h264_nvenc" in out_e
    return {
        "status": "ok",
        "msg": "ffmpeg present",
        "nvenc": nvenc,
        "nvenc_msg": (
            "NVENC encoder detected"
            if nvenc
            else "NVENC not detected (fallback to CPU likely)"
        ),
    }


def check_backups(cfg) -> Dict[str, Any]:
    bdir = cfg["BACKUP_DIR"]
    p = Path(bdir)
    if not p.exists():
        return _warn("Backup directory missing", path=bdir)

    fresh = _recent_file_in(bdir, cfg["BACKUP_FRESH_HOURS"])
    free = _drive_free_bytes(bdir)
    if fresh:
        return _ok(
            "Recent backup found",
            latest=str(fresh),
            fresh_within_hours=cfg["BACKUP_FRESH_HOURS"],
            free_bytes_on_drive=free,
        )
    return _warn(
        "No recent backup file",
        fresh_within_hours=cfg["BACKUP_FRESH_HOURS"],
        free_bytes_on_drive=free,
    )


def check_allowlist_and_ssl(cfg) -> Dict[str, Any]:
    allow = Path(cfg["ALLOWLIST_FILE"])
    al_status = allow.exists()
    cert_ok = Path(cfg["SSL_CERT"]).exists()
    key_ok = Path(cfg["SSL_KEY"]).exists()
    state = "ok" if (al_status and cert_ok and key_ok) else "warn"
    issues = []
    if not al_status:
        issues.append("allowlist missing")
    if not cert_ok:
        issues.append("ssl cert missing")
    if not key_ok:
        issues.append("ssl key missing")
    return {
        "status": state,
        "msg": "Security artefacts present" if state == "ok" else ", ".join(issues),
        "allowlist": allow.as_posix(),
        "cert": cfg["SSL_CERT"],
        "key": cfg["SSL_KEY"],
    }


def check_quiet_hours(cfg) -> Dict[str, Any]:
    now = datetime.now().hour
    start, end = cfg["QUIET_HOURS_START"], cfg["QUIET_HOURS_END"]
    in_quiet = start <= now < end if start < end else (now >= start or now < end)
    return _ok("Quiet hours respected", in_quiet=in_quiet, start=start, end=end)


def check_admin_privileges() -> Dict[str, Any]:
    return (
        _ok("Admin privileges present")
        if _is_admin_windows()
        else _warn("Not running as Administrator on Windows")
    )


def overall_status(items: Dict[str, Dict[str, Any]]) -> Tuple[str, int]:
    states = [v["status"] for v in items.values()]
    if "fail" in states:
        return "fail", 2
    if "warn" in states:
        return "warn", 1
    return "ok", 0


def run_all(cfg=CFG) -> Dict[str, Any]:
    checks = {
        "app_port": check_app_port(cfg),
        "sqlite": check_sqlite(cfg),
        "meilisearch": check_meilisearch(cfg),
        "cache": check_cache(cfg),
        "videos_sidecars": check_videos_and_sidecars(cfg),
        "ffmpeg": check_ffmpeg(cfg),
        "backups": check_backups(cfg),
        "security": check_allowlist_and_ssl(cfg),
        "quiet_hours": check_quiet_hours(cfg),
        "admin": check_admin_privileges(),
    }
    status, code = overall_status(checks)
    return {
        "status": status,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "host": socket.gethostname(),
        "config": {
            "app_host": cfg["APP_HOST"],
            "app_port": cfg["APP_PORT"],
            "db_path": cfg["DB_PATH"],
            "videos_dir": cfg["VIDEOS_DIR"],
            "cache_dir": cfg["CACHE_DIR"],
            "cache_cap": _bytes_fmt(cfg["CACHE_CAP_BYTES"]),
            "backup_dir": cfg["BACKUP_DIR"],
            "meili": f"{cfg['MEILI_HOST']}:{cfg['MEILI_PORT']}",
            "index": cfg["INDEX_NAME"],
        },
        "checks": checks,
        "exit_code": code,
    }


# ---------- CLI ----------
if __name__ == "__main__":
    res = run_all(CFG)
    print(json.dumps(res, indent=2))
    sys.exit(res["exit_code"])

# ---------- Optional FastAPI route ----------
try:
    from fastapi import APIRouter, Response

    router = APIRouter()

    @router.get("/healthz", tags=["health"])
    def healthz():
        data = run_all(CFG)
        code = (
            200
            if data["status"] == "ok"
            else (206 if data["status"] == "warn" else 503)
        )
        return Response(
            content=json.dumps(data), media_type="application/json", status_code=code
        )

except Exception:
    # FastAPI not installed — ignore
    router = None
