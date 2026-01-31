import unittest
from unittest.mock import MagicMock, patch
from agent.controller import AgentController, AgentState
from agent.planner import Plan, PlanStep

class TestAgentLoop(unittest.TestCase):
    
    def setUp(self):
        self.controller = AgentController()

    @patch('agent.planner.Planner.generate_plan')
    @patch('context.indexer.RepoIndexer.index')
    @patch('agent.executor.AgentExecutor.execute_step')
    def test_golden_path_success(self, mock_execute, mock_index, mock_plan):
        """
        Simulate a perfect run (Golden Repo #1 Success Trace)
        """
        # Mock Plan
        mock_plan.return_value = Plan(
            steps=[PlanStep(1, "Do work", "COMMAND", "echo work")],
            validation_strategy="Run tests"
        )
        # Mock Context
        mock_index.return_value = {"files": [], "root": "/tmp"}
        # Mock Execution
        mock_execute.return_value = MagicMock(success=True, output="Done")
        
        # Run
        final_state = self.controller.run("Fix the bug in main.py", "/tmp/repo")
        
        # Verify Final State
        self.assertEqual(final_state, AgentState.COMPLETED)
        
        # Verify Transition History (Sample checks)
        history = [entry['next_state'] for entry in self.controller.state_machine._execution_history]
        self.assertIn("RECEIVED_TASK", history)
        self.assertIn("PLANNING", history)
        self.assertIn("PLAN_VALIDATED", history)
        self.assertIn("CONTEXT_READY", history)
        self.assertIn("EXECUTING_STEP", history)
        self.assertIn("STEP_COMPLETED", history)
        self.assertIn("TESTING", history)
        self.assertIn("TESTS_PASSED", history)
        self.assertIn("COMPLETED", history)

    def test_planning_failure_stop(self):
        """
        Simulate ambiguity triggering STOPPED_SAFE
        """
        # Run with ambiguous task (Planner raises error internally or we assume behavior)
        # Our real Planner raises PlannerError on <3 words.
        
        final_state = self.controller.run("Fix bug", "/tmp/repo") # Ambiguous
        
        self.assertEqual(final_state, AgentState.STOPPED_SAFE)
        last_entry = self.controller.state_machine._execution_history[-1]
        self.assertIn("Planning failure", last_entry['reason'])

    @patch('agent.planner.Planner.generate_plan')
    @patch('context.indexer.RepoIndexer.index')
    @patch('agent.executor.AgentExecutor.execute_step')
    def test_execution_failure_stop(self, mock_execute, mock_index, mock_plan):
        """
        Simulate execution failure + max retries -> STOPPED_SAFE
        """
        mock_plan.return_value = Plan(
            steps=[PlanStep(1, "Fail step", "COMMAND", "exit 1")],
            validation_strategy="Run tests"
        )
        mock_index.return_value = {}
        
        # Force failure
        mock_execute.return_value = MagicMock(success=False, error="Command failed")
        
        # Set max_retries to 0 for quick fail
        self.controller.reflection.max_retries = 0
        
        final_state = self.controller.run("Do complex task", "/tmp/repo")
        
        self.assertEqual(final_state, AgentState.STOPPED_SAFE)
        
        history = [entry['next_state'] for entry in self.controller.state_machine._execution_history]
        self.assertIn("EXECUTING_STEP", history)
        self.assertIn("TESTS_FAILED", history) # Step failure maps to this in current logic? 
        # Wait, in controller.py: 
        # if result.success: ... else: transition_to(AgentState.TESTS_FAILED, ...)
        # So yes.
        self.assertIn("REFLECTING", history)
        self.assertIn("STOPPED_SAFE", history)

if __name__ == '__main__':
    unittest.main()
