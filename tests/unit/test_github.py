import unittest
from unittest.mock import MagicMock, patch
from github.parser import CommandParser
from github.handler import WebhookHandler
from github.templates import ACKNOWLEDGEMENT_MSG

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
    @patch('github.handler.shutil.rmtree')
    @patch('github.handler.tempfile.mkdtemp')
    @patch('github.handler.subprocess.run')
    @patch('github.handler.PRBuilder.push_branch')
    @patch('github.handler.PRBuilder.commit_changes')
    @patch('github.handler.PRBuilder.create_branch')
    @patch('github.handler.PRBuilder.create_pr_via_api')
    @patch('github.client.GitHubClient.post_comment')
    @patch('github.client.GitHubClient.authenticate')
    @patch('github.client.GitHubClient.get_token')
    @patch('agent.controller.AgentController.run')
    def test_handler_flow_success(self, mock_run, mock_get_token, mock_auth, 
                                   mock_post_comment, mock_create_pr, mock_create_branch,
                                   mock_commit, mock_push, mock_subprocess, 
                                   mock_mkdtemp, mock_rmtree):
        from agent.state_machine import AgentState
        from github.pr_builder import PRResult
        
        # Setup mocks
        handler = WebhookHandler()
        mock_run.return_value = AgentState.COMPLETED
        mock_auth.return_value = True
        mock_get_token.return_value = "fake-token"
        mock_mkdtemp.return_value = "/tmp/kita-test"
        mock_push.return_value = True
        mock_create_pr.return_value = PRResult(success=True, pr_number=42, pr_url="https://github.com/user/repo/pull/42")
        
        payload = {
            "action": "created",
            "comment": {"body": "@kita implement this"},
            "issue": {"number": 1, "title": "Task", "body": "Details"},
            "repository": {"full_name": "user/repo"},
            "installation": {"id": 12345}
        }
        
        # Act
        handler.handle_event("issue_comment", payload)
        
        # Assert
        mock_auth.assert_called_with(12345)
        self.assertTrue(mock_post_comment.called)
        self.assertTrue(mock_run.called)
        mock_rmtree.assert_called()

    @patch('github.client.GitHubClient.authenticate')
    @patch('github.client.GitHubClient.post_comment')
    def test_handler_invalid_command_reply(self, mock_post_comment, mock_auth):
        mock_auth.return_value = True
        
        handler = WebhookHandler()
        payload = {
            "action": "created",
            "comment": {"body": "@kita do something cool"}, # Invalid grammar
            "issue": {"number": 2},
            "repository": {"full_name": "user/repo"},
            "installation": {"id": 123}
        }
        
        handler.handle_event("issue_comment", payload)
        
        # Should reply with rejection (now with repo_full_name as 3rd arg)
        mock_post_comment.assert_called_with(2, "Command not recognized. Try '@kita help'.", "user/repo")

if __name__ == '__main__':
    unittest.main()

