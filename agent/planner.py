from dataclasses import dataclass
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class PlanStep:
    id: int
    description: str
    action_type: str # 'COMMAND' or 'EDIT' or 'TEST'
    target: str      # file path or command string

@dataclass
class Plan:
    steps: List[PlanStep]
    validation_strategy: str

class PlannerError(Exception):
    pass

class Planner:
    """
    Bible III, Section 4: Planner Role
    Must create explicit, ordered plans.
    Must NOT execute code.
    """
    
    def generate_plan(self, task: str) -> Plan:
        """
        Generates a plan from a task description.
        In a real scenario, this would call an LLM.
        For V0 skeleton, we act as a strict gateway.
        """
        if not task:
            raise PlannerError("Task cannot be empty.")
            
        # Bible III, Section 4: Ambiguous task -> STOP
        if len(task.split()) < 3: # Simple heuristic for ambiguity in V0
             # In real impl, LLM would classify ambiguity.
             logger.error("Planning halted: Ambiguous task.")
             raise PlannerError("Task is too ambiguous. Please provide more detail.")

        # Mocking a simple plan for skeleton validity
        # Real implementation would parse LLM output.
        return Plan(
            steps=[], 
            validation_strategy="Run existing tests."
        )
