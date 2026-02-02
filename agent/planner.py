from dataclasses import dataclass
from typing import List, Optional
import json
import logging
from agent.state_machine import AgentState
from llm.client import LiteLLMClient, LLMClient, MockLLMClient
from llm.prompts import PLANNER_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    id: int
    description: str
    action_type: str  # 'COMMAND' or 'EDIT' or 'TEST'
    target: str  # file path or command string
    details: str = ""  # Content for valid edits


@dataclass
class Plan:
    steps: List[PlanStep]
    validation_strategy: str


class PlannerError(Exception):
    pass


class Planner:
    """
    Bible III, Section 4: Planner Role
    Must create explicit, ordered plans using LLM Intelligence.
    """

    def __init__(
        self,
        llm: Optional[LLMClient] = None,
        api_key: str = None,
        model: str = None,
        api_base: str = None,
    ):
        """
        Initialize the Planner.

        Args:
            llm: Optional pre-configured LLM client
            api_key: Optional API key for BYOK support
            model: Optional model override (e.g., "gpt-4-turbo", "claude-3-opus")
            api_base: Optional custom API endpoint (e.g., Azure OpenAI, local LLM)
        """
        import os

        # Check explicit mock request first
        if os.getenv("USE_MOCK_LLM") == "true":
            logger.info("USE_MOCK_LLM is set. Using MockLLMClient.")
            self.llm = MockLLMClient()
            return

        # Use provided LLM or create one with BYOK support
        if llm:
            self.llm = llm
        else:
            model_name = model or os.getenv("LLM_MODEL", "gpt-4-turbo")
            self.llm = LiteLLMClient(
                model=model_name, api_key=api_key, api_base=api_base
            )

        # Fallback to Mock if LiteLLM not available
        if isinstance(self.llm, LiteLLMClient) and not self.llm.litellm:
            logger.warning(
                "LiteLLM not installed. Swapping to MockLLMClient for safety."
            )
            self.llm = MockLLMClient()

    def generate_plan(self, task: str, context: str) -> Plan:
        """
        Generates a plan from a task description and repo context.
        """
        if not task:
            raise PlannerError("Task cannot be empty.")

        logger.info(f"Generating plan for task: {task}")

        # Construct Messages
        messages = [
            {
                "role": "system",
                "content": PLANNER_SYSTEM_PROMPT.format(context=context, task=task),
            },
            {"role": "user", "content": "Please generate the plan."},
        ]

        # Call LLM
        try:
            response_text = self.llm.complete(messages, temperature=0.1)
            return self._parse_llm_response(response_text)
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            raise PlannerError(f"LLM Planning failed: {e}")

    def _parse_llm_response(self, response_text: str) -> Plan:
        try:
            # Simple JSON cleanup for V0 (remove markdown fences if present)
            clean_text = response_text.strip()
            if clean_text.startswith("```"):
                clean_text = clean_text.split("\n", 1)[1]
            if clean_text.endswith("```"):
                clean_text = clean_text.rsplit("\n", 1)[0]

            data = json.loads(clean_text)

            steps = []
            for step_data in data.get("steps", []):
                steps.append(
                    PlanStep(
                        id=step_data.get("id"),
                        description=step_data.get("description"),
                        action_type=step_data.get("action_type"),
                        target=step_data.get("target"),
                        details=step_data.get("details", ""),
                    )
                )

            return Plan(
                steps=steps, validation_strategy=data.get("strategy", "Run tests")
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {response_text}")
            raise PlannerError(f"Invalid JSON from LLM: {e}")
