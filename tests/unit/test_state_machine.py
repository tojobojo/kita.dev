import unittest
from agent.state_machine import AgentState, StateMachine, TransitionError

class TestStateMachine(unittest.TestCase):
    def setUp(self):
        self.sm = StateMachine()

    def test_initial_state(self):
        self.assertEqual(self.sm.current_state, AgentState.IDLE)

    def test_valid_transitions(self):
        # Happy path trace (Bible IV Section 7 success trace roughly)
        self.sm.transition_to(AgentState.RECEIVED_TASK, "Task received")
        self.assertEqual(self.sm.current_state, AgentState.RECEIVED_TASK)

        self.sm.transition_to(AgentState.NORMALIZED, "Task normalized")
        self.assertEqual(self.sm.current_state, AgentState.NORMALIZED)

        self.sm.transition_to(AgentState.PLANNING, "Starting planning")
        self.assertEqual(self.sm.current_state, AgentState.PLANNING)

        self.sm.transition_to(AgentState.PLAN_VALIDATED, "Plan validated")
        self.assertEqual(self.sm.current_state, AgentState.PLAN_VALIDATED)

        self.sm.transition_to(AgentState.CONTEXT_BUILDING, "Building context")
        self.assertEqual(self.sm.current_state, AgentState.CONTEXT_BUILDING)
        
        self.sm.transition_to(AgentState.CONTEXT_READY, "Context ready")
        self.assertEqual(self.sm.current_state, AgentState.CONTEXT_READY)

        self.sm.transition_to(AgentState.EXECUTING_STEP, "Executing step")
        self.assertEqual(self.sm.current_state, AgentState.EXECUTING_STEP)

        self.sm.transition_to(AgentState.STEP_COMPLETED, "Step done")
        self.assertEqual(self.sm.current_state, AgentState.STEP_COMPLETED)
        
        self.sm.transition_to(AgentState.TESTING, "Running tests")
        self.assertEqual(self.sm.current_state, AgentState.TESTING)

        self.sm.transition_to(AgentState.TESTS_PASSED, "Tests passed")
        self.assertEqual(self.sm.current_state, AgentState.TESTS_PASSED)

        self.sm.transition_to(AgentState.COMPLETED, "Task completed")
        self.assertEqual(self.sm.current_state, AgentState.COMPLETED)

    def test_forbidden_transitions(self):
        # IDLE -> PLANNING is forbidden
        with self.assertRaises(TransitionError):
            self.sm.transition_to(AgentState.PLANNING, "Skipping ahead")
        
        # EXECUTING_STEP -> PLANNING is explicitly forbidden
        self.sm._current_state = AgentState.EXECUTING_STEP
        with self.assertRaises(TransitionError):
            self.sm.transition_to(AgentState.PLANNING, "Backtracking")

        # COMPLETED -> ANY is forbidden
        self.sm._current_state = AgentState.COMPLETED
        with self.assertRaises(TransitionError):
            self.sm.transition_to(AgentState.IDLE, "Restarting")

    def test_force_error_stop(self):
        self.sm.force_error_stop("Emergency stop")
        self.assertEqual(self.sm.current_state, AgentState.STOPPED_ERROR)
        
        # Check reasons
        last_entry = self.sm._execution_history[-1]
        self.assertEqual(last_entry["next_state"], "STOPPED_ERROR")
        self.assertEqual(last_entry["reason"], "FORCED STOP: Emergency stop")

    def test_missing_reason(self):
        with self.assertRaises(ValueError):
            self.sm.transition_to(AgentState.RECEIVED_TASK, "")

if __name__ == '__main__':
    unittest.main()
