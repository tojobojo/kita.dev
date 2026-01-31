# Bible VI, Section 3, 5, 6, 7

ACKNOWLEDGEMENT_MSG = """👋 I’m Kita.dev.
I’m reviewing this task and will create a plan.
I’ll stop if anything is unclear or unsafe."""

# Bible VI, Section 7: PR Creation Rules
PR_BODY_TEMPLATE = """
## Summary
{summary}

## Implementation Details
{implementation_details}

## Files Changed
{files_changed}

## Tests Run
{tests_run}

## Risks
{risks}

## Confidence Score
{confidence_score}
"""

STOP_MSG_TEMPLATE = """I stopped to avoid making an unsafe or incorrect change.
STOP is not an error.
STOP is a correct outcome.

Reason: {reason}"""

FAILURE_MSG_TEMPLATE = """## Task Failed
**What failed:** {what_failed}
**Why it failed:** {why_failed}
**Retry possible:** {retry_possible}
**Next steps:** {next_steps}"""
