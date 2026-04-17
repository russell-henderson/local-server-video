"""Archived manage_subs CLI (historical copy).

This archived copy retains the last compatibility shim that documented
the original CLI behaviour. The live repository no longer ships the
full subtitle generation backend.
"""
import sys


def main():
    print("Subtitle system: REMOVED. The subtitle CLI is archived and unavailable.")
    print(
        "To re-enable subtitle generation, restore the original implementation or see archive/python_legacy/."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
