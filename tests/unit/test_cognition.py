import unittest
from agent.planner import Planner, PlannerError, Plan
from agent.executor import AgentExecutor, ExecutionResult, PlanStep
from agent.reflection import ReflectionEngine, Decision
from agent.confidence import ConfidenceEvaluator

class TestCognition(unittest.TestCase):
    
    # --- Planner Tests ---
    def test_planner_ambiguity(self):
        planner = Planner()
        # "Fix bug" is too short < 3 words
        with self.assertRaises(PlannerError):
            planner.generate_plan("Fix bug")
            
    def test_planner_valid(self):
        planner = Planner()
        plan = planner.generate_plan("Fix the login bug")
        self.assertIsInstance(plan, Plan)

    # --- Executor Tests ---
    def test_executor_single_step(self):
        executor = AgentExecutor()
        step = PlanStep(id=1, description="echo hello", action_type="COMMAND", target="echo hello")
        result = executor.execute_step(step)
        self.assertTrue(result.success)
        
    def test_executor_invalid_step(self):
        executor = AgentExecutor()
        result = executor.execute_step("Not a step object")
        self.assertFalse(result.success)

    # --- Reflection Tests ---
    def test_reflection_continue(self):
        engine = ReflectionEngine()
        result = ExecutionResult(True, "OK")
        decision = engine.reflect(result)
        self.assertEqual(decision.decision, Decision.CONTINUE)

    def test_reflection_retry_limit(self):
        engine = ReflectionEngine(max_retries=1)
        result = ExecutionResult(False, "Fail")
        
        # 1st failure -> RETRY
        d1 = engine.reflect(result)
        self.assertEqual(d1.decision, Decision.RETRY)
        
        # 2nd failure -> STOP (Max 1 exceeded)
        d2 = engine.reflect(result)
        self.assertEqual(d2.decision, Decision.STOP)

    # --- Confidence Tests ---
    def test_confidence_decay(self):
        evaluator = ConfidenceEvaluator()
        history = [
            ExecutionResult(True, "OK"),
            ExecutionResult(False, "Fail"),
            ExecutionResult(True, "Fixed")
        ]
        score = evaluator.evaluate(history)
        # 2 success, 1 fail. Success rate = 2/3 = 0.66
        # Penalty applied? Yes.
        self.assertLess(score, 1.0)
        self.assertGreater(score, 0.0)

if __name__ == '__main__':
    unittest.main()
