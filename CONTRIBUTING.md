# Contributing to healtheval

We welcome contributions from healthcare AI engineers, clinical informaticists,
and RCM specialists.

## What We Need Most

- **New failure modes** — observed a clinical AI failure not in the current 10? Open an issue.
- **Better deterministic checks** — improved regex, edge case handling, broader drug lists.
- **Clinical validation** — if you can validate severity ratings, open an issue.
- **New agent categories** — gaps include care management, scheduling, patient communication.

## How to Contribute a Failure Mode

1. Fork the repository
2. Add YAML to appropriate file in `failure_modes/`
3. Add deterministic check function in `healtheval/deterministic.py`
4. Register it in `DETERMINISTIC_REGISTRY`
5. Add at least 2 test cases (FAIL + PASS) to `tests/fixtures/sample_cases.yaml`
6. Add unit tests to `tests/test_deterministic.py`
7. Open a Pull Request

## ID Convention

Format: `CATEGORY-NNN` (next sequential number for that category)
Categories: `SCRIBE`, `RCM`, `REFILL`, `FAXROUTE`, `PRIORAUTH`, `CAREMANAGEMENT`, `SCHEDULING`

## Rules

- **No PHI** — all examples must be synthetic
- **No claims of clinical validation** — engineering tool, not certified system
- **Severity ratings must be clinically grounded** — explain reasoning in PR

## Dev Setup

```bash
git clone https://github.com/versionone-health/healtheval
cd healtheval
pip install -e ".[dev]"
pytest tests/ -v
healtheval list
```

## License

By contributing, you agree your contributions are licensed under Apache 2.0.
