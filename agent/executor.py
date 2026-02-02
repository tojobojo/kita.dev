from dataclasses import dataclass
from typing import Any
import logging
from agent.planner import PlanStep

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    success: bool
    output: str
    error: str = ""


class ExecutorError(Exception):
    pass


class AgentExecutor:
    """
    Bible III, Section 5: Executor Role
    Must execute exactly one step.
    Must NOT plan, reflect, or loop.
    """

    def execute_step(self, step: PlanStep, repo_path: str) -> ExecutionResult:
        """
        Executes a single step from the plan.
        """
        try:
            if not isinstance(step, PlanStep):
                raise ExecutorError("Invalid step type provided.")

            logger.info(f"EXECUTING STEP {step.id}: {step.description}")

            # Dispatch based on action type
            if step.action_type == "COMMAND":
                return self._execute_command_step(step, repo_path)
            elif step.action_type == "EDIT":
                return self._execute_edit_step(step, repo_path)
            else:
                return ExecutionResult(
                    False, "", f"Unknown action type: {step.action_type}"
                )

        except Exception as e:
            return ExecutionResult(False, "", str(e))

    def _execute_command_step(self, step: PlanStep, repo_path: str) -> ExecutionResult:
        from sandbox.executor import SandboxExecutor

        sandbox = SandboxExecutor()
        result = sandbox.run(step.target, repo_path)

        return ExecutionResult(
            success=result.exit_code == 0, output=result.stdout, error=result.stderr
        )

    def _execute_edit_step(self, step: PlanStep, repo_path: str) -> ExecutionResult:
        import os

        # Security Check: Prevent path traversal
        full_path = os.path.abspath(os.path.join(repo_path, step.target))
        if not full_path.startswith(os.path.abspath(repo_path)):
            return ExecutionResult(
                False, "", f"Security Error: Path traversal attempt to {step.target}"
            )

        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(step.details)  # details contains the code content

            logger.info(f"Wrote file: {full_path}")
            return ExecutionResult(True, f"Successfully wrote to {step.target}")

        except Exception as e:
            return ExecutionResult(False, "", f"Failed to write file: {e}")
