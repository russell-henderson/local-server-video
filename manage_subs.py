"""Minimal compatibility stub for manage_subs (archived).

The original CLI helper was archived to `archive/python_legacy/manage_subs.py`.
This compact stub prevents ImportError for scripts that import
`manage_subs` but no longer require the full CLI.
"""

import sys
import warnings

warnings.warn(
    "manage_subs module archived to archive/python_legacy/manage_subs.py",
    DeprecationWarning,
)


def main():
    print("Subtitle CLI is archived and unavailable.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
