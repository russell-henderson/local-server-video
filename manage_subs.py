"""manage_subs.py — subtitle management CLI (REMOVED)

The automatic subtitle generation system has been removed from the
application. This script previously provided CLI helpers to check and
generate subtitles. It now only prints a notice to avoid ImportError
or confusion.
"""

import sys


def main():
    print("Subtitle system: REMOVED. The subtitle CLI is unavailable.")
    print(
        "To re-enable subtitle generation, restore the original implementation"
    )
    print("or see docs/deferred/ for archived documentation.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
