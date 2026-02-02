"""
GitHub Event Dispatcher
Bible VI: Routes events to agent controller.
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from github.webhooks import WebhookEvent, WebhookRouter
from github.parser import CommandParser, Command
from github.handler import WebhookHandler

logger = logging.getLogger(__name__)

@dataclass
class DispatchResult:
    handled: bool
    job_id: Optional[str]
    message: str

class EventDispatcher:
    """
    Central dispatcher for GitHub webhook events.
    Routes to appropriate handlers based on event type and content.
    """
    
    def __init__(self):
        self.router = WebhookRouter()
        self.parser = CommandParser()
        self.handler = WebhookHandler()
        
    def dispatch(self, event: WebhookEvent) -> DispatchResult:
        """
        Dispatches a webhook event to the appropriate handler.
        
        Returns:
            DispatchResult with handling status
        """
        # Check if event is supported
        if not self.router.is_supported(event):
            logger.info(f"Ignoring unsupported event: {event.event_type}/{event.action}")
            return DispatchResult(
                handled=False,
                job_id=None,
                message=f"Event type {event.event_type}/{event.action} not supported"
            )
        
        # Extract context
        context = self.router.extract_context(event)
        logger.info(f"Dispatching event from {context['sender']} on {context['repository']['full_name']}")
        
        # Route based on event type
        if event.event_type == "issue_comment":
            return self._handle_issue_comment(event, context)
        elif event.event_type == "issues":
            return self._handle_issue(event, context)
        elif event.event_type == "pull_request_review_comment":
            return self._handle_pr_comment(event, context)
        else:
            return DispatchResult(
                handled=False,
                job_id=None,
                message=f"No handler for {event.event_type}"
            )
    
    def _handle_issue_comment(self, event: WebhookEvent, context: Dict[str, Any]) -> DispatchResult:
        """Handles issue comment events."""
        comment_body = context.get("comment", {}).get("body", "")
        
        # Check for bot mention
        if not comment_body.strip().lower().startswith("@kita"):
            return DispatchResult(
                handled=False,
                job_id=None,
                message="Comment does not mention @kita"
            )
        
        # Parse command
        command = self.parser.parse(comment_body)
        if not command:
            # Invalid command - respond with help
            logger.info(f"Invalid command: {comment_body}")
            return DispatchResult(
                handled=True,
                job_id=None,
                message="Command not recognized. Valid commands: @kita implement this, @kita retry, @kita stop"
            )
        
        # Dispatch based on command action
        logger.info(f"Dispatching command: {command.action}")
        
        # Delegate to WebhookHandler
        self.handler.handle_event(event.event_type, event.payload)
        
        return DispatchResult(
            handled=True,
            job_id="pending",  # Handler manages job IDs
            message=f"Command {command.action} dispatched"
        )
    
    def _handle_issue(self, event: WebhookEvent, context: Dict[str, Any]) -> DispatchResult:
        """Handles issue created/edited events."""
        # Check if issue has kita label
        issue_labels = context.get("issue", {}).get("labels", [])
        
        if "kita" not in issue_labels and "kita-auto" not in issue_labels:
            return DispatchResult(
                handled=False,
                job_id=None,
                message="Issue does not have kita label"
            )
        
        logger.info(f"Auto-processing labeled issue: {context['issue']['number']}")
        # Could auto-trigger agent here for labeled issues
        
        return DispatchResult(
            handled=True,
            job_id=None,
            message="Labeled issue noted (auto-processing not enabled in V0)"
        )
    
    def _handle_pr_comment(self, event: WebhookEvent, context: Dict[str, Any]) -> DispatchResult:
        """Handles PR review comment events."""
        # Similar to issue comment handling
        comment_body = context.get("comment", {}).get("body", "")
        
        if not comment_body.strip().lower().startswith("@kita"):
            return DispatchResult(
                handled=False,
                job_id=None,
                message="PR comment does not mention @kita"
            )
        
        return DispatchResult(
            handled=True,
            job_id=None,
            message="PR comment commands not fully implemented in V0"
        )
