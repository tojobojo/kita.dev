from enum import Enum
from dataclasses import dataclass
from agent.executor import ExecutionResult


class Decision(Enum):
    CONTINUE = "CONTINUE"
    RETRY = "RETRY"
    STOP = "STOP"


@dataclass
class ReflectionDecision:
    decision: Decision
    reason: str
    retry_modifications: str = ""


class ReflectionEngine:
    """
    Bible III, Section 6: Reflection Engine
    Analyzes execution results.
    Decides Retry vs STOP.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.current_retries = 0

    def reflect(self, result: ExecutionResult) -> ReflectionDecision:
        """
        Analyzes the result of a step execution.
        """
        if result.success:
            return ReflectionDecision(Decision.CONTINUE, "Step succeeded.")

        # Failure handling
        self.current_retries += 1

        # Bible III, Section 7: Retries beyond limit -> STOP
        if self.current_retries > self.max_retries:
            return ReflectionDecision(
                Decision.STOP, f"Max retries ({self.max_retries}) exceeded."
            )

        return ReflectionDecision(
            Decision.RETRY,
            f"Step failed with error: {result.error}. Retrying ({self.current_retries}/{self.max_retries}).",
        )
