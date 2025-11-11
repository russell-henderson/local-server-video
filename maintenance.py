#!/usr/bin/env python3
"""
DEPRECATED: maintenance.py has been moved to tools/safe_maintenance.py

To run maintenance commands, use:
  python tools/safe_maintenance.py <command>

Original documentation is preserved in tools/safe_maintenance.py.
"""
import warnings

warnings.warn(
    "maintenance.py is deprecated. Use tools/safe_maintenance.py instead.",
    DeprecationWarning,
    stacklevel=2
)

print("Error: maintenance.py has been moved to tools/safe_maintenance.py")
print("Please run: python tools/safe_maintenance.py <command>")
