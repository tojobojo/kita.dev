import unittest
import os
import shutil
import tempfile
from agent.executor import AgentExecutor
from agent.planner import PlanStep

class TestExecutorPersistence(unittest.TestCase):
    def setUp(self):
        self.executor = AgentExecutor()
        self.test_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_file_creation(self):
        step = PlanStep(
            id=1,
            description="Create file",
            action_type="EDIT",
            target="hello.txt",
            details="Hello World"
        )
        
        result = self.executor.execute_step(step, self.test_dir)
        
        self.assertTrue(result.success)
        file_path = os.path.join(self.test_dir, "hello.txt")
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r") as f:
            content = f.read()
            self.assertEqual(content, "Hello World")

    def test_nested_file_creation(self):
        step = PlanStep(
            id=2,
            description="Create nested file",
            action_type="EDIT",
            target="src/utils/helper.py",
            details="print('helper')"
        )
        
        result = self.executor.execute_step(step, self.test_dir)
        
        self.assertTrue(result.success)
        file_path = os.path.join(self.test_dir, "src/utils/helper.py")
        self.assertTrue(os.path.exists(file_path))
        
    def test_path_traversal_prevention(self):
        step = PlanStep(
            id=3,
            description="Attack",
            action_type="EDIT",
            target="../evil.txt",
            details="malware"
        )
        
        result = self.executor.execute_step(step, self.test_dir)
        
        self.assertFalse(result.success)
        self.assertIn("Security Error", result.error)
