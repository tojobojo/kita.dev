import logging
import tempfile
import shutil
import os
import subprocess
from typing import Dict, Any

from github.parser import CommandParser
from github.client import GitHubClient
from github.pr_builder import PRBuilder, PRSpec
from github.templates import (
    ACKNOWLEDGEMENT_MSG,
    STOP_MSG_TEMPLATE,
    FAILURE_MSG_TEMPLATE,
)
from agent.controller import AgentController, AgentState

logger = logging.getLogger(__name__)


class WebhookHandler:
    """
    Handles supported entry points (Issue Comments).
    Orchestrates the Agent Controller based on webhook events.
    Now with Real Git Operations!
    """

    def __init__(self):
        self.parser = CommandParser()
        self.gh = GitHubClient()
        self.controller = AgentController()
        # Pass client to PRBuilder
        self.pr_builder = PRBuilder(self.gh)

    def handle_event(self, event_type: str, payload: Dict[str, Any]):
        """
        Process incoming GitHub webhooks.
        """
        if event_type != "issue_comment":
            return

        action = payload.get("action")
        if action != "created":
            return

        comment = payload.get("comment", {})
        issue = payload.get("issue", {})

        body = comment.get("body", "")
        issue_number = issue.get("number")
        repo_data = payload.get("repository", {})
        repo_full_name = repo_data.get("full_name")
        installation_id = payload.get("installation", {}).get("id")

        # 1. Parse Command
        command = self.parser.parse(body)
        if not command:
            if body.strip().lower().startswith("@kita"):
                # Simple auth check for posting failure
                if self.gh.authenticate(installation_id):
                    self.gh.post_comment(
                        issue_number,
                        "Command not recognized. Try '@kita help'.",
                        repo_full_name,
                    )
            return

        # 2. Authenticate
        if not installation_id:
            logger.error("No installation ID found in webhook")
            return

        if not self.gh.authenticate(installation_id):
            logger.error(f"Authentication failed for installation {installation_id}")
            return

        # 3. Acknowledge
        self.gh.post_comment(issue_number, ACKNOWLEDGEMENT_MSG, repo_full_name)

        # 4. Prepare Workspace (Clone)
        work_dir = tempfile.mkdtemp(prefix="kita-run-")
        logger.info(f"Created workspace: {work_dir}")

        try:
            token = self.gh.get_token()
            clone_url = (
                f"https://x-access-token:{token}@github.com/{repo_full_name}.git"
            )

            # Clone
            subprocess.run(["git", "clone", clone_url, "."], cwd=work_dir, check=True)

            # Configure Git
            subprocess.run(
                ["git", "config", "user.name", "Kita Bot"], cwd=work_dir, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "bot@kita.dev"],
                cwd=work_dir,
                check=True,
            )

            # Create Branch
            branch_name = f"kita/issue-{issue_number}"
            # Ensure we start fresh or handle checkouts
            self.pr_builder.create_branch(work_dir, branch_name)

            # 5. Extract Task
            task_description = f"{issue.get('title', '')}\n\n{issue.get('body', '')}"
            if command.args:
                task_description += f"\n\nExtra instructions: {command.args}"

            # 6. Run Agent
            if command.action == "IMPLEMENT":
                final_state = self.controller.run(task_description, work_dir)
                self._handle_completion(
                    issue_number, final_state, work_dir, branch_name, repo_full_name
                )

            elif command.action == "STOP":
                self.gh.post_comment(issue_number, "Stop received.", repo_full_name)

        except Exception as e:
            logger.exception("Workflow failed")
            self.gh.post_comment(
                issue_number, f"💥 **System Error**: {str(e)}", repo_full_name
            )
        finally:
            # Cleanup
            shutil.rmtree(work_dir)
            logger.info(f"Cleaned up workspace: {work_dir}")

    def _handle_completion(
        self,
        issue_number: int,
        state: AgentState,
        work_dir: str,
        branch_name: str,
        repo_full_name: str,
    ):
        if state == AgentState.COMPLETED:
            # Commit all changes made by agent
            self.pr_builder.commit_changes(
                work_dir, [], f"Fix for issue #{issue_number}"
            )

            # Push
            if self.pr_builder.push_branch(work_dir, branch_name):
                # Create PR
                summary = "Task completed by Kita.dev"

                # Get stats from controller
                history = self.controller.get_history()
                # Try to extract useful stats if available, else usage placeholders

                spec = PRSpec(
                    title=f"Kita: Fix for Issue #{issue_number}",
                    body=self.pr_builder.format_pr_body(
                        summary=summary,
                        implementation_details="Autonomous changes.",
                        files_changed=["(See file diff)"],
                        tests_run="Verification Logic Passed",
                        risks="Review generated code.",
                        confidence_score=1.0,
                    ),
                    head_branch=branch_name,
                    base_branch="main",  # Default
                    files=[],  # Files already committed
                )

                res = self.pr_builder.create_pr_via_api(spec, repo_full_name)
                if res.success:
                    self.gh.post_comment(
                        issue_number,
                        f"✅ **Task Completed!**\n\nPR Opened: {res.pr_url}",
                        repo_full_name,
                    )
                else:
                    self.gh.post_comment(
                        issue_number,
                        f"⚠️ **Task Completed but PR Failed**\n\nError: {res.error}",
                        repo_full_name,
                    )
            else:
                self.gh.post_comment(
                    issue_number, "⚠️ Failed to push changes to branch.", repo_full_name
                )

        elif state == AgentState.STOPPED_SAFE:
            self.gh.post_comment(
                issue_number,
                STOP_MSG_TEMPLATE.format(reason="Safety check triggered."),
                repo_full_name,
            )

        elif state == AgentState.STOPPED_ERROR:
            self.gh.post_comment(
                issue_number,
                FAILURE_MSG_TEMPLATE.format(
                    what_failed="Agent Execution",
                    why_failed="Internal error",
                    retry_possible="Unknown",
                    next_steps="Check logs",
                ),
                repo_full_name,
            )
