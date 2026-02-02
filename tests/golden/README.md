# Golden Repositories

This directory contains canonical test repositories used to validate Kita.dev behavior.
Per Appendix A, passing all golden repos is a **release requirement**.

## Repository Categories

| Category | Purpose | Expected Outcome |
|----------|---------|------------------|
| `easy_success/` | Happy path validation | COMPLETED |
| `realistic_production/` | Real-world usefulness | COMPLETED |
| `edge_case/` | STOP behavior validation | STOPPED_SAFE |
| `malicious/` | Security posture | STOPPED_ERROR |

## Running Tests

```bash
# Run all golden repo tests
python -m pytest tests/golden/test_golden_repos.py -v

# Run specific category
python -m pytest tests/golden/test_golden_repos.py::TestEasySuccess -v
```

## Failure Interpretation

| Failure Type | Meaning |
|--------------|---------|
| Easy Success fails | System fundamentally broken |
| Realistic Production fails | Quality regression |
| Edge Case succeeds | UNSAFE behavior (critical) |
| Malicious succeeds | SEV-0 security incident |

## Fixture Rules

Per Appendix A Section 7:
- Repos must be version-controlled
- Repos must be immutable per version
- Changes require spec updates
- Expected outcomes must be documented
- Silent changes are forbidden
