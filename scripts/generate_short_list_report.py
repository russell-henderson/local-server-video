from __future__ import annotations

import html
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SHORT-LIST.md"
TARGET = ROOT / "SHORT-LIST.html"


def parse_rows(markdown: str) -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    table_row = re.compile(r"^\| \[(.+?)\]\((.+?)\) \| \[(.+?)\]\((.+?)\) \| (.+?) \|$")
    for line in markdown.splitlines():
        match = table_row.match(line.strip())
        if not match:
            continue
        file_name = match.group(1)
        path = match.group(2)
        modified = match.group(5)
        rows.append((file_name, path, modified))
    return rows


def build_html(rows: list[tuple[str, str, str]]) -> str:
    escaped_rows = []
    for file_name, path, modified in rows:
        escaped_rows.append(
            "<tr>"
            f"<td data-label=\"File\"><a href=\"{html.escape(path, quote=True)}\">{html.escape(file_name)}</a></td>"
            f"<td data-label=\"Path\"><a href=\"{html.escape(path, quote=True)}\">{html.escape(path)}</a></td>"
            f"<td data-label=\"Last Modified Date\" data-sort-value=\"{html.escape(modified, quote=True)}\">{html.escape(modified)}</td>"
            "</tr>"
        )

    row_count = len(rows)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Short List</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f5f7fb;
      --panel: #ffffff;
      --text: #172033;
      --muted: #5b6475;
      --line: #d7deea;
      --accent: #2457d6;
      --accent-soft: #eaf0ff;
      --shadow: 0 12px 30px rgba(18, 32, 61, 0.08);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Segoe UI, Arial, sans-serif;
      background: linear-gradient(180deg, #eef3ff 0%, var(--bg) 28%, #eef2f8 100%);
      color: var(--text);
    }}
    .wrap {{ max-width: 1400px; margin: 0 auto; padding: 28px 18px 40px; }}
    .hero {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px 22px;
      box-shadow: var(--shadow);
      position: sticky;
      top: 0;
      z-index: 5;
      backdrop-filter: blur(8px);
    }}
    .hero h1 {{ margin: 0 0 8px; font-size: 28px; }}
    .hero p {{ margin: 0 0 16px; color: var(--muted); line-height: 1.45; }}
    .stats {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }}
    .stat {{ background: var(--accent-soft); color: var(--accent); padding: 8px 12px; border-radius: 999px; font-weight: 600; }}
    .controls {{ display: grid; gap: 10px; grid-template-columns: repeat(3, minmax(0, 1fr)); }}
    .controls label {{ display: grid; gap: 6px; font-size: 13px; font-weight: 600; color: var(--muted); }}
    .controls input {{
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 10px 12px;
      font: inherit;
      background: #fff;
      color: var(--text);
    }}
    .controls input:focus {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
    .table-card {{
      margin-top: 18px;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: var(--shadow);
      overflow: hidden;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    thead th {{
      position: sticky;
      top: 148px;
      background: #f8fbff;
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 14px 16px;
      white-space: nowrap;
    }}
    thead button {{
      border: 0;
      padding: 0;
      background: transparent;
      color: var(--text);
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }}
    thead button:hover {{ color: var(--accent); }}
    tbody td {{ padding: 12px 16px; border-bottom: 1px solid var(--line); vertical-align: top; }}
    tbody tr:hover {{ background: #f8fbff; }}
    tbody a {{ color: var(--accent); text-decoration: none; }}
    tbody a:hover {{ text-decoration: underline; }}
    .hidden {{ display: none; }}
    .footer {{ margin-top: 14px; color: var(--muted); font-size: 13px; }}
    @media (max-width: 900px) {{
      .controls {{ grid-template-columns: 1fr; }}
      thead {{ display: none; }}
      table, tbody, tr, td {{ display: block; width: 100%; }}
      tbody tr {{ border-bottom: 1px solid var(--line); padding: 10px 0; }}
      tbody td {{ border: 0; padding: 8px 16px; }}
      tbody td::before {{
        content: attr(data-label);
        display: block;
        font-size: 12px;
        color: var(--muted);
        font-weight: 700;
        margin-bottom: 4px;
      }}
    }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <section class=\"hero\">
      <h1>Short List</h1>
      <p>Interactive view for files that are not ignored by either ignore file and are older than 45 days. Use the filters before selecting anything for backup.</p>
      <div class=\"stats\">
        <div class=\"stat\" id=\"visibleCount\">0 visible</div>
        <div class=\"stat\">{row_count} total</div>
        <div class=\"stat\">Generated {generated_at}</div>
      </div>
      <div class=\"controls\">
        <label>Filter file
          <input id=\"fileFilter\" type=\"search\" placeholder=\"Type part of a file name\" />
        </label>
        <label>Filter path
          <input id=\"pathFilter\" type=\"search\" placeholder=\"Type part of a path\" />
        </label>
        <label>Filter date
          <input id=\"dateFilter\" type=\"search\" placeholder=\"YYYY-MM or year\" />
        </label>
      </div>
    </section>

    <section class=\"table-card\">
      <table id=\"shortListTable\">
        <thead>
          <tr>
            <th><button type=\"button\" data-sort=\"file\">File</button></th>
            <th><button type=\"button\" data-sort=\"path\">Path</button></th>
            <th><button type=\"button\" data-sort=\"modified\">Last Modified Date</button></th>
          </tr>
        </thead>
        <tbody>
          {''.join(escaped_rows)}
        </tbody>
      </table>
    </section>

    <div class=\"footer\">Click the headers to sort. Use the search fields to narrow the shortlist before you back up anything.</div>
  </div>

  <script>
    const table = document.getElementById('shortListTable');
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const visibleCount = document.getElementById('visibleCount');
    const fileFilter = document.getElementById('fileFilter');
    const pathFilter = document.getElementById('pathFilter');
    const dateFilter = document.getElementById('dateFilter');
    const sortState = {{ column: 'modified', direction: 'desc' }};

    function getCellText(row, index) {{
      return row.children[index].textContent.trim().toLowerCase();
    }}

    function getModifiedValue(row) {{
      return row.children[2].dataset.sortValue || row.children[2].textContent.trim();
    }}

    function renderRows() {{
      const fileQuery = fileFilter.value.trim().toLowerCase();
      const pathQuery = pathFilter.value.trim().toLowerCase();
      const dateQuery = dateFilter.value.trim().toLowerCase();
      let count = 0;

      rows.forEach((row) => {{
        const fileText = getCellText(row, 0);
        const pathText = getCellText(row, 1);
        const dateText = getCellText(row, 2);
        const match =
          (!fileQuery || fileText.includes(fileQuery)) &&
          (!pathQuery || pathText.includes(pathQuery)) &&
          (!dateQuery || dateText.includes(dateQuery));
        row.classList.toggle('hidden', !match);
        if (match) count += 1;
      }});

      visibleCount.textContent = `${{count}} visible`;
    }}

    function sortRows(column) {{
      if (sortState.column === column) {{
        sortState.direction = sortState.direction === 'asc' ? 'desc' : 'asc';
      }} else {{
        sortState.column = column;
        sortState.direction = column === 'modified' ? 'desc' : 'asc';
      }}

      rows.sort((a, b) => {{
        let left;
        let right;
        if (column === 'modified') {{
          left = getModifiedValue(a);
          right = getModifiedValue(b);
        }} else if (column === 'path') {{
          left = getCellText(a, 1);
          right = getCellText(b, 1);
        }} else {{
          left = getCellText(a, 0);
          right = getCellText(b, 0);
        }}

        if (left < right) return sortState.direction === 'asc' ? -1 : 1;
        if (left > right) return sortState.direction === 'asc' ? 1 : -1;
        return 0;
      }});

      rows.forEach((row) => tbody.appendChild(row));
      renderRows();
    }}

    fileFilter.addEventListener('input', renderRows);
    pathFilter.addEventListener('input', renderRows);
    dateFilter.addEventListener('input', renderRows);

    table.querySelectorAll('button[data-sort]').forEach((button) => {{
      button.addEventListener('click', () => sortRows(button.dataset.sort));
    }});

    sortRows('modified');
    renderRows();
  </script>
</body>
</html>
"""


def main() -> None:
    rows = parse_rows(SOURCE.read_text(encoding="utf-8"))
    TARGET.write_text(build_html(rows), encoding="utf-8")
    print(f"Wrote {TARGET} with {len(rows)} rows")


if __name__ == "__main__":
    main()