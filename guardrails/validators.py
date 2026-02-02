"""
Guardrails Validators Module
Bible II, Section 5: Soft checks, risk heuristics.
"""

import re
import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class ValidationResult:
    passed: bool
    risk_level: RiskLevel
    warnings: List[str]
    blockers: List[str]


class TaskValidator:
    """
    Validates tasks before execution.
    Soft checks that may warn or block based on risk.
    """

    # Patterns that suggest scope expansion
    SCOPE_EXPANSION_PATTERNS = [
        r"\brefactor\s+(?:the\s+)?entire\b",
        r"\brewrite\s+(?:the\s+)?whole\b",
        r"\bupgrade\s+all\b",
        r"\bchange\s+everything\b",
        r"\bfix\s+all\b",
    ]

    # Patterns suggesting unsafe operations
    UNSAFE_PATTERNS = [
        r"\bdelete\s+(?:the\s+)?database\b",
        r"\bdrop\s+table\b",
        r"\brm\s+-rf\b",
        r"\bformat\s+(?:the\s+)?disk\b",
        r"\bwipe\b",
        r"\bpurge\s+all\b",
    ]

    # Vague task patterns (Bible III Section 14: Bad Reasoning Example)
    VAGUE_PATTERNS = [
        r"^improve\s+performance$",
        r"^make\s+it\s+faster$",
        r"^optimize$",
        r"^fix\s+bugs$",
        r"^clean\s+up\s+code$",
        r"^make\s+it\s+better$",
    ]

    def validate_task(self, task: str) -> ValidationResult:
        """
        Validates a task description.
        Returns validation result with risk assessment.
        """
        warnings = []
        blockers = []

        task_lower = task.lower().strip()

        # Check for vague tasks
        for pattern in self.VAGUE_PATTERNS:
            if re.match(pattern, task_lower, re.IGNORECASE):
                blockers.append(
                    f"Task is too vague: '{task}'. Please provide specific requirements."
                )

        # Check for scope expansion
        for pattern in self.SCOPE_EXPANSION_PATTERNS:
            if re.search(pattern, task_lower, re.IGNORECASE):
                blockers.append(
                    f"Task implies scope expansion. Please narrow the scope."
                )

        # Check for unsafe operations
        for pattern in self.UNSAFE_PATTERNS:
            if re.search(pattern, task_lower, re.IGNORECASE):
                blockers.append(
                    f"Task contains potentially unsafe operation. Requires manual review."
                )

        # Check task length (too short = likely vague)
        if len(task.split()) < 3:
            warnings.append(
                "Task description is very short. Consider adding more detail."
            )

        # Check task length (too long = might be multiple tasks)
        if len(task.split()) > 100:
            warnings.append(
                "Task description is very long. Consider breaking into smaller tasks."
            )

        # Determine risk level
        if blockers:
            risk_level = RiskLevel.CRITICAL
        elif len(warnings) >= 2:
            risk_level = RiskLevel.HIGH
        elif warnings:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW

        passed = len(blockers) == 0

        if not passed:
            logger.warning(f"Task validation failed: {blockers}")
        elif warnings:
            logger.info(f"Task validation passed with warnings: {warnings}")

        return ValidationResult(
            passed=passed, risk_level=risk_level, warnings=warnings, blockers=blockers
        )


class PlanValidator:
    """
    Validates execution plans before running.
    """

    MAX_STEPS = 10  # Reasonable limit for V0

    def validate_plan(self, steps: List[dict]) -> ValidationResult:
        """
        Validates a plan's steps.
        """
        warnings = []
        blockers = []

        # Check step count
        if len(steps) == 0:
            blockers.append("Plan has no steps.")
        elif len(steps) > self.MAX_STEPS:
            blockers.append(
                f"Plan has too many steps ({len(steps)}). Maximum is {self.MAX_STEPS}."
            )

        # Check each step
        for step in steps:
            step_id = step.get("id", "?")
            action_type = step.get("action_type", "")
            target = step.get("target", "")

            # Validate action type
            if action_type not in ["COMMAND", "EDIT", "TEST"]:
                blockers.append(f"Step {step_id}: Invalid action type '{action_type}'")

            # Validate target
            if not target:
                blockers.append(f"Step {step_id}: Missing target")

            # Check for dangerous commands
            if action_type == "COMMAND":
                if any(
                    danger in target.lower()
                    for danger in ["rm -rf", "sudo", "chmod 777"]
                ):
                    blockers.append(f"Step {step_id}: Dangerous command detected")

            # Check for path traversal in EDIT
            if action_type == "EDIT":
                if ".." in target:
                    blockers.append(
                        f"Step {step_id}: Path traversal detected in target"
                    )

        # Determine risk
        if blockers:
            risk_level = RiskLevel.CRITICAL
        elif len(steps) > 5:
            risk_level = RiskLevel.MEDIUM
            warnings.append("Plan has many steps. Execution may take longer.")
        else:
            risk_level = RiskLevel.LOW

        return ValidationResult(
            passed=len(blockers) == 0,
            risk_level=risk_level,
            warnings=warnings,
            blockers=blockers,
        )


class OutputValidator:
    """
    Validates command/execution output for safety.
    """

    # Patterns that suggest errors we should catch
    ERROR_PATTERNS = [
        r"permission\s+denied",
        r"access\s+denied",
        r"not\s+found",
        r"no\s+such\s+file",
        r"command\s+not\s+found",
        r"syntax\s+error",
        r"traceback",
        r"exception",
        r"fatal\s+error",
    ]

    def validate_output(self, stdout: str, stderr: str) -> Tuple[bool, List[str]]:
        """
        Validates command output.
        Returns (is_safe, issues).
        """
        issues = []
        combined = (stdout + stderr).lower()

        for pattern in self.ERROR_PATTERNS:
            if re.search(pattern, combined, re.IGNORECASE):
                issues.append(f"Output contains error pattern: {pattern}")

        # Check for size (might indicate runaway process)
        if len(combined) > 1_000_000:  # 1MB
            issues.append("Output is unusually large (>1MB)")

        return len(issues) == 0, issues
