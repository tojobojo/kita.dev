# Golden Repository #2: Realistic Production

## Purpose
Validate real-world usefulness - measures actual product value.

## Structure
```
realistic_production/
├── src/
│   ├── __init__.py
│   ├── app.py             # Flask application
│   ├── auth.py            # Authentication logic
│   ├── database.py        # Database layer
│   └── models.py          # Data models
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   └── test_models.py
├── requirements.txt
└── README.md
```

## Test Cases

### Task 1: Feature Addition
**Issue:** "Add a password reset feature to auth.py"
**Expected Outcome:**
- ✅ Feature added with proper structure
- ✅ Tests pass
- ✅ PR created
- ✅ No scope expansion

### Task 2: Bug Fix with Regression Test
**Issue:** "Fix the token expiration bug - tokens don't expire"
**Expected Outcome:**
- ✅ Bug fixed
- ✅ Regression test added
- ✅ PR created

### Task 3: Scoped Refactor
**Issue:** "Extract the email validation logic into a separate module"
**Expected Outcome:**
- ✅ Refactor completed
- ✅ No functionality changes
- ✅ Tests pass

## Failure Interpretation
Failure here indicates quality regression.
