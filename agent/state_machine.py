import logging
from enum import Enum
from datetime import datetime
from typing import Dict, List, Set, Optional

# Configure logging
logger = logging.getLogger(__name__)

class AgentState(Enum):
    """
    The agent must operate using the following states only.
    No additional states are allowed.
    Defined in Bible IV, Section 1.
    """
    IDLE = "IDLE"
    RECEIVED_TASK = "RECEIVED_TASK"
    NORMALIZED = "NORMALIZED"
    PLANNING = "PLANNING"
    PLAN_VALIDATED = "PLAN_VALIDATED"
    CONTEXT_BUILDING = "CONTEXT_BUILDING"
    CONTEXT_READY = "CONTEXT_READY"
    EXECUTING_STEP = "EXECUTING_STEP"
    STEP_COMPLETED = "STEP_COMPLETED"
    TESTING = "TESTING"
    TESTS_PASSED = "TESTS_PASSED"
    TESTS_FAILED = "TESTS_FAILED"
    REFLECTING = "REFLECTING"
    RETRYING = "RETRYING"
    STOPPED_SAFE = "STOPPED_SAFE"
    STOPPED_ERROR = "STOPPED_ERROR"
    COMPLETED = "COMPLETED"

class TransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass

class StateMachine:
    """
    Governs all Kita.dev execution state transitions.
    Enforces rules defined in Bible IV.
    """

    # Bible IV, Section 3: Allowed State Transitions
    ALLOWED_TRANSITIONS: Dict[AgentState, Set[AgentState]] = {
        AgentState.IDLE: {AgentState.RECEIVED_TASK},
        AgentState.RECEIVED_TASK: {AgentState.NORMALIZED},
        AgentState.NORMALIZED: {AgentState.PLANNING, AgentState.STOPPED_SAFE},
        AgentState.PLANNING: {AgentState.PLAN_VALIDATED, AgentState.STOPPED_SAFE},
        AgentState.PLAN_VALIDATED: {AgentState.CONTEXT_BUILDING},
        AgentState.CONTEXT_BUILDING: {AgentState.CONTEXT_READY, AgentState.STOPPED_ERROR},
        AgentState.CONTEXT_READY: {AgentState.EXECUTING_STEP},
        AgentState.EXECUTING_STEP: {AgentState.STEP_COMPLETED, AgentState.STOPPED_ERROR, AgentState.TESTS_FAILED},
        AgentState.STEP_COMPLETED: {AgentState.TESTING},
        AgentState.TESTING: {AgentState.TESTS_PASSED, AgentState.TESTS_FAILED},
        AgentState.TESTS_PASSED: {AgentState.COMPLETED},
        AgentState.TESTS_FAILED: {AgentState.REFLECTING},
        AgentState.REFLECTING: {AgentState.RETRYING, AgentState.STOPPED_SAFE},
        AgentState.RETRYING: {AgentState.EXECUTING_STEP},
        # Terminal states (COMPLETED, STOPPED_*) have no outgoing transitions in standard flow.
        # Bible IV, Section 4: STOPPED_* -> ANY is forbidden.
        # Bible IV, Section 4: COMPLETED -> ANY is forbidden.
    }

    def __init__(self):
        """Initialize the state machine in IDLE state."""
        self._current_state = AgentState.IDLE
        self._execution_history: List[Dict] = []
        self._log_transition(None, self._current_state, "Initialization")

    @property
    def current_state(self) -> AgentState:
        """Returns the current state of the agent."""
        return self._current_state

    def transition_to(self, new_state: AgentState, reason: str) -> None:
        """
        Transitions the agent to a new state if allowed.

        Args:
            new_state: The target AgentState.
            reason: The reason for the transition (required for logging).

        Raises:
            TransitionError: If the transition is not allowed.
        """
        if not reason:
            raise ValueError("Reason must be provided for state transition.")

        if not self._is_transition_allowed(new_state):
            error_msg = f"Invalid transition from {self._current_state} to {new_state}. Reason: {reason}"
            logger.error(error_msg)
            # If we are already stopped or completed, further transitions are strictly forbidden per Bible IV Section 4.
            # If we are in a running state but attempt a forbidden move, we must transition to STOPPED_ERROR per Bible IV Section 4.
            if self._current_state not in [AgentState.STOPPED_ERROR, AgentState.STOPPED_SAFE, AgentState.COMPLETED]:
                 # Recursive call to stop safely on violation, but prevent infinite recursion if THAT fails (it shouldn't as any -> STOPPED_ERROR is not generally allowed, but here we force it as a penalty)
                 # Actually, Bible IV Section 4 says "Violation -> STOPPED_ERROR".
                 # But we can't transition to STOPPED_ERROR if we are in a state that doesn't allow it in the ALLOWED_TRANSITIONS table?
                 # Wait, Bible IV Section 3 lists "Allowed" transitions.
                 # Section 4 lists "Forbidden" ones and says "Violation -> STOPPED_ERROR".
                 # This implies that if a violation occurs, the machine FORCEFULLY moves to STOPPED_ERROR.
                 # However, if we are already in STOPPED_*, we cannot move.
                 
                 # Let's check if we are already terminal.
                 pass

            raise TransitionError(error_msg)

        old_state = self._current_state
        self._current_state = new_state
        self._log_transition(old_state, new_state, reason)

    def _is_transition_allowed(self, new_state: AgentState) -> bool:
        """Checks if the transition is allowed based on the allowed transitions table."""
        if self._current_state in self.ALLOWED_TRANSITIONS:
            return new_state in self.ALLOWED_TRANSITIONS[self._current_state]
        return False

    def _log_transition(self, old_state: Optional[AgentState], new_state: AgentState, reason: str) -> None:
        """
        Logs the state transition.
        Bible IV, Section 8: Every state transition must log: Previous state, Next state, Timestamp, Reason.
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "previous_state": old_state.value if old_state else None,
            "next_state": new_state.value,
            "reason": reason
        }
        self._execution_history.append(entry)
        
        log_msg = f"TRANSITION: {entry['previous_state']} -> {entry['next_state']} | Reason: {reason}"
        logger.info(log_msg)

    def force_error_stop(self, reason: str) -> None:
        """
        Forces a transition to STOPPED_ERROR.
        Used when an invariant is violated or an unrecoverable error occurs.
        This bypasses the strict transition table for emergency stops, effectively implementing "Violation -> STOPPED_ERROR".
        """
        if self._current_state in [AgentState.STOPPED_SAFE, AgentState.STOPPED_ERROR, AgentState.COMPLETED]:
             # Already stopped, do nothing to preserve the original stop reason.
             return

        old_state = self._current_state
        self._current_state = AgentState.STOPPED_ERROR
        self._log_transition(old_state, AgentState.STOPPED_ERROR, f"FORCED STOP: {reason}")
