"""Persistent gallery snapshots and bounded, versioned thumbnail generation.

No group records are deleted here. A failed directory scan never publishes absence.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps

EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
SIZES = (160, 320, 640, 1280)
RECIPE = 'webp-alpha-exif-v3-q82'


def contained_path(root: Path, name: str) -> Path:
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Invalid media path')
    base = root.resolve()
    candidate = (base / name).resolve()
    if candidate == base or not candidate.is_relative_to(base):
        raise ValueError('Media path escapes library')
    return candidate


class GalleryIndex:
    def __init__(self, source: Path, output: Path, database: Path, interval=30):
        self.source, self.output, self.database = (Path(p).resolve() for p in (source, output, database))
        self.interval = interval
        self._lock = threading.RLock()
        self._scanning = False
        self._done = threading.Event()
        self._done.set()
        self._last_attempt = 0
        self._error = None
        self._pending = set()
        self._failures = {}
        self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix='gallery-thumbs')
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS assets (name TEXT PRIMARY KEY, metadata TEXT NOT NULL, available INTEGER NOT NULL)')
            self._records = {name: json.loads(meta) for name, meta in db.execute('SELECT name, metadata FROM assets WHERE available=1')}
        self._publish()

    def _connect(self):
        return sqlite3.connect(self.database, timeout=30)

    def _publish(self):
        names = sorted(self._records, key=lambda name: (name.casefold(), name))
        version = hashlib.sha256(json.dumps(self._records, sort_keys=True).encode()).hexdigest()[:20]
        self._snapshot = {'version': version, 'images': names, 'total': len(names), 'image_meta': dict(self._records)}

    def status(self):
        with self._lock:
            return {'refreshing': self._scanning, 'error': self._error,
                    'pending_thumbnails': len(self._pending), 'thumbnail_errors': dict(self._failures)}

    def snapshot(self):
        with self._lock:
            needs_initial_scan = not self._records and not self._scanning
        if needs_initial_scan:
            self.refresh(force=True, wait=True)
        elif self._scanning:
            self._done.wait()
        with self._lock:
            return {**self._snapshot, 'status': self.status()}

    def refresh(self, force=False, wait=False):
        if wait:
            self._done.wait()
        with self._lock:
            if self._scanning or (not force and time.monotonic() - self._last_attempt < self.interval):
                return False
            self._scanning = True
            self._done.clear()
            self._last_attempt = time.monotonic()
        if wait:
            self._scan()
        else:
            threading.Thread(target=self._scan, daemon=True, name='gallery-index').start()
        return True

    def _scan(self):
        try:
            # Missing/unmounted roots raise; never reinterpret an outage as an empty library.
            entries = list(self.source.iterdir())
            with self._connect() as db:
                old = {name: json.loads(meta) for name, meta in db.execute('SELECT name, metadata FROM assets')}
            records = {}
            for path in entries:
                if path.suffix.lower() not in EXTENSIONS or not path.is_file():
                    continue
                contained_path(self.source, path.name)
                stat = path.stat()
                previous = old.get(path.name, {})
                revision = hashlib.sha256(f'{path.name}:{stat.st_size}:{stat.st_mtime_ns}:{RECIPE}'.encode()).hexdigest()[:20]
                if previous.get('revision') == revision:
                    records[path.name] = previous
                    continue
                meta = {'bytes': stat.st_size, 'modified': stat.st_mtime_ns,
                        'added': previous.get('added', stat.st_mtime_ns if not old else time.time_ns()),
                        'revision': revision, 'width': 0, 'height': 0, 'animated': False,
                        'format': path.suffix[1:].lower()}
                try:
                    with Image.open(path) as image:
                        meta['animated'] = bool(getattr(image, 'is_animated', False))
                        meta['width'], meta['height'] = ImageOps.exif_transpose(image).size
                        meta['format'] = (image.format or meta['format']).lower()
                except (OSError, ValueError) as exc:
                    meta['error'] = f'Cannot decode image: {exc}'
                # A source changing mid-read invalidates the whole scan; retry later.
                if path.stat().st_mtime_ns != stat.st_mtime_ns:
                    raise OSError('Library changed during scan; refresh again')
                records[path.name] = meta
            with self._connect() as db:
                db.execute('UPDATE assets SET available=0')
                db.executemany('INSERT INTO assets VALUES (?, ?, 1) ON CONFLICT(name) DO UPDATE SET metadata=excluded.metadata, available=1',
                               [(name, json.dumps(meta)) for name, meta in records.items()])
            with self._lock:
                self._records = records
                self._error = None
                self._publish()
        except (OSError, ValueError, sqlite3.Error) as exc:
            with self._lock:
                self._error = str(exc)
        finally:
            with self._lock:
                self._scanning = False
                self._done.set()

    def derivative(self, name, size):
        if size not in SIZES:
            raise ValueError('Unsupported thumbnail size')
        contained_path(self.source, name)
        with self._lock:
            meta = self._records.get(name)
            if not meta:
                raise FileNotFoundError(name)
            revision = meta['revision']
        target = self.output / revision / f'{size}.webp'
        if target.is_file():
            return target, revision
        key = (name, revision)
        with self._lock:
            if key not in self._pending and len(self._pending) < 160 and not meta.get('error'):
                self._pending.add(key)
                self._pool.submit(self._build, name, meta)
        return None, revision

    def _build(self, name, meta):
        key = (name, meta['revision'])
        try:
            path = contained_path(self.source, name)
            with Image.open(path) as original:
                original.seek(0)
                image = ImageOps.exif_transpose(original).convert('RGBA' if 'A' in original.getbands() or 'transparency' in original.info else 'RGB')
                directory = self.output / meta['revision']
                directory.mkdir(parents=True, exist_ok=True)
                for size in SIZES:
                    target = directory / f'{size}.webp'
                    if target.exists():
                        continue
                    thumb = image.copy()
                    thumb.thumbnail((size, size), Image.Resampling.LANCZOS)
                    temporary = target.with_suffix(f'.{uuid.uuid4().hex}.tmp')
                    try:
                        thumb.save(temporary, 'WEBP', quality=82, method=4)
                        stat = path.stat()
                        if stat.st_mtime_ns != meta['modified'] or stat.st_size != meta['bytes']:
                            raise OSError('Source changed during thumbnail generation')
                        os.replace(temporary, target)
                    finally:
                        temporary.unlink(missing_ok=True)
            with self._lock:
                self._failures.pop(name, None)
        except (OSError, ValueError) as exc:
            with self._lock:
                self._failures[name] = str(exc)
        finally:
            with self._lock:
                self._pending.discard(key)

    def close(self):
        self._done.wait()
        self._pool.shutdown(wait=True)
