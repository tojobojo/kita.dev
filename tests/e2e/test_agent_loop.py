import unittest
import tempfile
import os
from unittest.mock import MagicMock, patch
from agent.controller import AgentController, AgentState
from agent.planner import Plan, PlanStep

# Use mock LLM for testing
os.environ["USE_MOCK_LLM"] = "true"


class TestAgentLoop(unittest.TestCase):

    def setUp(self):
        self.controller = AgentController()
        # Create a temporary repo with a Python file for language detection
        self.temp_dir = tempfile.mkdtemp()
        # Add a Python file so language detection passes
        with open(os.path.join(self.temp_dir, "main.py"), "w") as f:
            f.write("# Main file\ndef main():\n    pass\n")
        with open(os.path.join(self.temp_dir, "requirements.txt"), "w") as f:
            f.write("pytest\n")

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("agent.planner.Planner.generate_plan")
    @patch("context.indexer.RepoIndexer.index")
    @patch("agent.executor.AgentExecutor.execute_step")
    def test_golden_path_success(self, mock_execute, mock_index, mock_plan):
        """
        Simulate a perfect run (Golden Repo #1 Success Trace)
        """
        # Mock Context (Now runs FIRST)
        mock_index.return_value = "Repo Context String"

        # Mock Plan (Now runs SECOND and takes context)
        mock_plan.return_value = Plan(
            steps=[PlanStep(1, "Do work", "COMMAND", "echo work")],
            validation_strategy="Run tests",
        )
        # Mock Execution
        mock_execute.return_value = MagicMock(success=True, output="Done")

        # Run with valid task (4+ words to pass validation)
        final_state = self.controller.run("Fix the bug in main.py", self.temp_dir)

        # Verify Final State
        self.assertEqual(final_state, AgentState.COMPLETED)

        # Verify Transition History (Sample checks)
        history = [
            entry["next_state"]
            for entry in self.controller.state_machine._execution_history
        ]
        self.assertIn("RECEIVED_TASK", history)
        self.assertIn("CONTEXT_READY", history)  # Context before Planning
        self.assertIn("PLANNING", history)
        self.assertIn("PLAN_VALIDATED", history)
        self.assertIn("EXECUTING_STEP", history)
        self.assertIn("STEP_COMPLETED", history)
        self.assertIn("TESTING", history)
        self.assertIn("TESTS_PASSED", history)
        self.assertIn("COMPLETED", history)

    def test_planning_failure_stop(self):
        """
        Simulate ambiguity triggering STOPPED_SAFE via task validation.
        Short/vague tasks are blocked by TaskValidator.
        """
        # Run with vague task - TaskValidator should catch this
        final_state = self.controller.run("fix bugs", self.temp_dir)  # Too vague

        # Should stop safely due to task validation
        self.assertEqual(final_state, AgentState.STOPPED_SAFE)

    @patch("agent.planner.Planner.generate_plan")
    @patch("context.indexer.RepoIndexer.index")
    @patch("agent.executor.AgentExecutor.execute_step")
    def test_execution_failure_stop(self, mock_execute, mock_index, mock_plan):
        """
        Simulate execution failure + max retries -> STOPPED_SAFE
        """
        mock_plan.return_value = Plan(
            steps=[PlanStep(1, "Fail step", "COMMAND", "exit 1")],
            validation_strategy="Run tests",
        )
        mock_index.return_value = "Context String"

        # Force failure
        mock_execute.return_value = MagicMock(success=False, error="Command failed")

        # Set max_retries to 0 for quick fail
        self.controller.reflection.max_retries = 0

        # Use valid task (4+ words)
        final_state = self.controller.run("Do a complex task here", self.temp_dir)

        self.assertEqual(final_state, AgentState.STOPPED_SAFE)

        history = [
            entry["next_state"]
            for entry in self.controller.state_machine._execution_history
        ]
        self.assertIn("EXECUTING_STEP", history)
        self.assertIn("TESTS_FAILED", history)
        self.assertIn("REFLECTING", history)
        self.assertIn("STOPPED_SAFE", history)


if __name__ == "__main__":
    unittest.main()
