#!/usr/bin/env python3
"""
Simple link checker for local (relative) links in Markdown and HTML files.
Checks that local file targets exist. Skips HTTP(S) links.
Exits with code 1 if missing links are found.
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

md_link_re = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
html_link_re = re.compile(r'href\s*=\s*"([^"]+)"')

missing = []
checked = 0

for dirpath, dirnames, filenames in os.walk(ROOT):
    # skip .git and .venv and node_modules
    parts = Path(dirpath).parts
    if any(part in (".git", ".venv", "venv", "node_modules") for part in parts):
        continue
    for fname in filenames:
        # Only check Markdown files; skip HTML and template files which contain Jinja or dynamic urls
        if not (fname.endswith('.md') or fname.endswith('.markdown')):
            continue
        fpath = Path(dirpath) / fname
        try:
            text = fpath.read_text(encoding='utf-8')
        except Exception:
            continue
        # Skip files that contain Jinja-style templating markers to avoid false positives
        if '{{' in text or '{%' in text:
            continue
        links = md_link_re.findall(text)
        for link in links:
            checked += 1
            link = link.strip()
            # skip empty
            if not link:
                continue
            # skip anchors and mailto
            if link.startswith('#') or link.startswith('mailto:'):
                continue
            # skip external
            if link.startswith('http://') or link.startswith('https://'):
                continue
            # for links with fragments, split
            target = link.split('#', 1)[0]
            # ignore data URIs
            if target.startswith('data:'):
                continue
            # if link is absolute (starts with /), treat relative to repo root
            if target.startswith('/'):
                candidate = (ROOT / target.lstrip('/')).resolve()
            else:
                candidate = (fpath.parent / target).resolve()
            # handle directory targets by checking for index.md or README.md
            if candidate.is_dir():
                idx1 = candidate / 'index.md'
                idx2 = candidate / 'README.md'
                if not (idx1.exists() or idx2.exists()):
                    missing.append((str(fpath.relative_to(ROOT)), link, str(candidate.relative_to(ROOT))))
            else:
                # if extension missing, allow .md or .html
                if not candidate.exists():
                    if not Path(str(candidate) + '.md').exists() and not Path(str(candidate) + '.html').exists():
                        missing.append((str(fpath.relative_to(ROOT)), link, str(candidate.relative_to(ROOT))))

print(f"Checked {checked} local links in markdown/html files under {ROOT}")
if missing:
    print('\nMissing local link targets:')
    for src, link, target in missing:
        print(f" - In {src}: '{link}' -> missing {target}")
    print(f"\nTotal missing: {len(missing)}")
    sys.exit(1)
else:
    print('No missing local links found.')
    sys.exit(0)
