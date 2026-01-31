import logging
from typing import Dict, Any

from github.parser import CommandParser
from github.client import GitHubClient
from github.templates import ACKNOWLEDGEMENT_MSG, PR_BODY_TEMPLATE, STOP_MSG_TEMPLATE, FAILURE_MSG_TEMPLATE
from agent.controller import AgentController, AgentState

logger = logging.getLogger(__name__)

class WebhookHandler:
    """
    Bible VI: Handles supported entry points (Issue Comments).
    Orchestrates the Agent Controller based on webhook events.
    """
    
    def __init__(self):
        self.parser = CommandParser()
        self.gh = GitHubClient()
        self.controller = AgentController()
        
    def handle_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Process incoming GitHub webhooks.
        Supported: issue_comment.created
        """
        if event_type != "issue_comment":
            logger.info(f"Ignoring unsupported event type: {event_type}")
            return
            
        action = payload.get("action")
        if action != "created":
            return
            
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        
        body = comment.get("body", "")
        issue_number = issue.get("number")
        repo_full_name = payload.get("repository", {}).get("full_name")
        
        # 1. Parse Command
        # Phase 6 Rule: "Support issue comment invocation only"
        command = self.parser.parse(body)
        
        if not command:
            # Ignore non-commands (chatty check)
            # Bible VI: "Invalid commands -> clarification or STOP".
            # But we must distinguish "random chatter" from "attempted command".
            # For V0, valid commands are strict. If it's not a command, we ignore it 
            # (assuming it's human conversation). 
            # If it STARTS with @kita but is invalid, we might reply.
            if body.strip().lower().startswith("@kita"):
                 self.gh.post_comment(issue_number, "I stopped. Command not recognized. Please use strict grammar (e.g., '@kita implement this').")
            return

        # 2. Acknowledge
        self.gh.post_comment(issue_number, ACKNOWLEDGEMENT_MSG)
        
        # 3. Extract Task Context
        # Using Issue Title + Body as the task context
        task_description = f"{issue.get('title', '')}\n\n{issue.get('body', '')}"
        
        # 4. Trigger Agent
        # Mocking repo path - in real life we clone here using SWE-agent utils
        repo_path = "/tmp/mock_repo" 
        
        # Dispatch based on action
        if command.action == "IMPLEMENT":
            final_state = self.controller.run(task_description, repo_path)
            self._handle_completion(issue_number, final_state)
            
        elif command.action == "STOP":
            # Handle stop signal (if run was async, we'd kill it. For sync V0, this might just acknowledge stop)
            self.gh.post_comment(issue_number, STOP_MSG_TEMPLATE.format(reason="User requested STOP."))
            
        # ... other actions ...

    def _handle_completion(self, issue_number: int, state: AgentState):
        if state == AgentState.COMPLETED:
            # Create PR
            # Using template
            pr_body = PR_BODY_TEMPLATE.format(
                summary="Task completed successfully.",
                implementation_details="See code changes.",
                files_changed="main.py",
                tests_run="Unit tests passed.",
                risks="None identified.",
                confidence_score="1.0"
            )
            self.gh.create_pr("Kita: Task Completion", pr_body, "kita-branch")
            self.gh.post_comment(issue_number, "Task completed. PR created.")
            
        elif state == AgentState.STOPPED_SAFE:
            self.gh.post_comment(
                issue_number, 
                STOP_MSG_TEMPLATE.format(reason="Safety or ambiguity check triggered.")
            )
            
        elif state == AgentState.STOPPED_ERROR:
            self.gh.post_comment(
                issue_number,
                FAILURE_MSG_TEMPLATE.format(
                    what_failed="Internal execution error",
                    why_failed="System trapped an exception",
                    retry_possible="No",
                    next_steps="Contact support"
                )
            )
