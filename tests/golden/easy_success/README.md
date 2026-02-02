# Golden Repository #1: Easy Success

## Purpose
Validate the happy path - if Kita.dev fails here, the system is fundamentally broken.

## Structure
```
easy_success/
├── src/
│   ├── __init__.py
│   ├── calculator.py      # Simple math operations
│   └── utils.py           # Helper functions
├── tests/
│   ├── __init__.py
│   └── test_calculator.py # Basic unit tests
├── requirements.txt
└── README.md
```

## Test Cases

### Task 1: Add a Function
**Issue:** "Add a `multiply(a, b)` function to calculator.py"
**Expected Outcome:**
- ✅ Function added correctly
- ✅ Tests pass
- ✅ PR created
- ✅ Confidence score > 0.8
- ✅ No STOP

### Task 2: Fix a Bug
**Issue:** "Fix the divide function - it doesn't handle zero division"
**Expected Outcome:**
- ✅ Bug fixed with proper exception handling
- ✅ Tests pass
- ✅ PR created
- ✅ No STOP

### Task 3: Add Tests
**Issue:** "Add unit tests for the subtract function"
**Expected Outcome:**
- ✅ Tests added
- ✅ All tests pass
- ✅ PR created
- ✅ No STOP

## Failure Interpretation
Any failure in this repository indicates a fundamental system break.
