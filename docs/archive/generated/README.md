# Generated Root Artifacts (Archived by Policy)

This folder records generated root-level artifacts that were removed from the repository root during cleanup.

Removed from root:

* `SHORT-LIST.md`
* `SHORT-LIST.html`
* `file-structure.txt`

Regeneration commands:

* Short list report: `python scripts/generate_short_list_report.py`
* Project structure export: `powershell -File scripts/export-project-structure.ps1`

Policy:

* Generated inventory/report outputs should not live at repository root.
* Keep generated artifacts in archive/generated docs paths, or regenerate on demand.
