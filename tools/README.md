# Tools Directory

Administrative scripts and utilities for the Local Video Server.

## Safe Tools

These tools are safe to run and won't delete data without explicit `--dry-run` confirmation.

### `safe_maintenance.py`

Unified maintenance tool for the video server.

```bash
python tools/safe_maintenance.py cleanup [--dry-run]       # Remove orphaned thumbnails and metadata
python tools/safe_maintenance.py thumbnails [--force]      # Regenerate video thumbnails
python tools/safe_maintenance.py sanitize [--dry-run]      # Clean up filenames
python tools/safe_maintenance.py test                      # Test database and cache
python tools/safe_maintenance.py all [--dry-run]           # Run all tasks
```

**Options**:

- `--dry-run`: Preview changes without applying them
- `--force`: Force regeneration of existing thumbnails

## Experimental Tools

(None currently. Prefix future experimental scripts with `experimental_`.)

## Archived Tools

Deprecated tools have been moved to `archive/python_legacy/`:

- `manage_subs.py` - Subtitle CLI (archived)
- `app_subs_integration.py` - Subtitle routes (archived)

These remain in the root as compatibility stubs to prevent import errors.
