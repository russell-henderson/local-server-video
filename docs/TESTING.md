# Testing

Two reporting surfaces are the official suite entry points:

- `tests/test_smoke_suite.py`
- `tests/test_regression_suite.py`

## Run Smoke Suite

```powershell
python -m pytest -q tests/test_smoke_suite.py
```

## Run Regression Suite

```powershell
python -m pytest -q tests/test_regression_suite.py
```

## Scope

Smoke suite checks app boot and protected route contracts.
Regression suite checks ratings/favorites/tags/admin/gallery baseline behavior.

Legacy fragmented suites have been retired; release validation and CI reporting now run only through the two suite files above.
