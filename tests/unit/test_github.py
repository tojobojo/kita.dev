import unittest
from unittest.mock import MagicMock, patch
from github.parser import CommandParser
from github.handler import WebhookHandler
from github.templates import ACKNOWLEDGEMENT_MSG, PR_BODY_TEMPLATE

class TestGitHubIntegration(unittest.TestCase):
    
    # --- Parser Tests ---
    def test_parser_valid(self):
        parser = CommandParser()
        cmd = parser.parse("@kita implement this")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.action, "IMPLEMENT")
        
    def test_parser_case_insensitive(self):
        parser = CommandParser()
        cmd = parser.parse("@KITA Implement THIS")
        self.assertIsNotNone(cmd)
        self.assertEqual(cmd.action, "IMPLEMENT")

    def test_parser_invalid(self):
        parser = CommandParser()
        self.assertIsNone(parser.parse("@kita please help")) # Natural language rejected
        self.assertIsNone(parser.parse("implement this")) # Missing mention

    # --- Handler Tests ---
    @patch('github.client.GitHubClient.post_comment')
    @patch('github.client.GitHubClient.create_pr')
    @patch('agent.controller.AgentController.run')
    def test_handler_flow_success(self, mock_run, mock_create_pr, mock_post_comment):
        from agent.state_machine import AgentState
        
        # Setup
        handler = WebhookHandler()
        mock_run.return_value = AgentState.COMPLETED
        
        payload = {
            "action": "created",
            "comment": {"body": "@kita implement this"},
            "issue": {"number": 1, "title": "Task", "body": "Details"},
            "repository": {"full_name": "user/repo"}
        }
        
        # Act
        handler.handle_event("issue_comment", payload)
        
        # Assert
        # 1. Acknowledgment
        # 2. Completion message / PR
        self.assertTrue(mock_post_comment.called)
        # Check ack message usage
        mock_post_comment.assert_any_call(1, ACKNOWLEDGEMENT_MSG)
        
        # Check PR creation
        self.assertTrue(mock_create_pr.called)
        args, _ = mock_create_pr.call_args
        self.assertIn("Kita: Task Completion", args[0])
        # Verify template usage in body
        self.assertIn("## Confidence Score", args[1])

    @patch('github.client.GitHubClient.post_comment')
    def test_handler_invalid_command_reply(self, mock_post_comment):
        handler = WebhookHandler()
        payload = {
            "action": "created",
            "comment": {"body": "@kita do something cool"}, # Invalid grammar
            "issue": {"number": 2},
        }
        
        handler.handle_event("issue_comment", payload)
        
        # Should reply with rejection
        mock_post_comment.assert_called_with(2, "I stopped. Command not recognized. Please use strict grammar (e.g., '@kita implement this').")

if __name__ == '__main__':
    unittest.main()
