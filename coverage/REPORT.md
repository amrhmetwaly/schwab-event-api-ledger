# Test coverage report

Generated: **2026-05-20 23:26 UTC**

Regenerate after code or test changes:

```bash
./scripts/coverage.sh
```

Interactive HTML (local only, not committed): `coverage/html/index.html`

## Summary

| Metric | Value |
|--------|------:|
| Tests collected | 81 |
| Statements | 358 |
| Lines covered | 358 |
| Lines missed | 0 |
| **Line coverage** | **100.0%** |
| Branch coverage | 100.0% (52/52) |

## Coverage by module (`event_ledger_api`)

| Module | Line % | Covered / Stmts | Uncovered lines |
|--------|-------:|----------------:|-----------------|
| `__init__.py` | 100.0% | 1/1 | — |
| `api.py` | 100.0% | 44/44 | — |
| `config.py` | 100.0% | 9/9 | — |
| `database.py` | 100.0% | 41/41 | — |
| `errors.py` | 100.0% | 33/33 | — |
| `main.py` | 100.0% | 22/22 | — |
| `models.py` | 100.0% | 18/18 | — |
| `money.py` | 100.0% | 22/22 | — |
| `schemas.py` | 100.0% | 65/65 | — |
| `services.py` | 100.0% | 103/103 | — |

## Test suite layout

| Directory | Tests (`def test_`) |
|-----------|--------------------:|
| `tests/contract` | 14 |
| `tests/integration` | 23 |
| `tests/unit` | 38 |

## Notes

- Coverage measures `src/event_ledger_api` only (application code under test).
- Regenerate with `./scripts/coverage.sh` after changes; `fail_under = 100` in `pyproject.toml`.
- Machine-readable detail: `coverage/coverage.json`.
