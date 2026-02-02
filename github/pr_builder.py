"""
GitHub PR Builder Module
Bible VI, Section 7: PR Creation Rules
"""
import os
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FileChange:
    path: str
    content: str
    mode: str = "100644"  # Regular file

@dataclass
class PRSpec:
    title: str
    body: str
    head_branch: str
    base_branch: str
    files: List[FileChange]
    
@dataclass
class PRResult:
    success: bool
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None

class PRBuilder:
    """
    Builds and creates Pull Requests.
    Bible VI, Section 7: PR Creation Rules
    """
    
    # Bible VI: PR title prefix
    TITLE_PREFIX = "Kita: "
    
    def __init__(self, github_client=None):
        self.client = github_client
        
    def validate_pr_spec(self, spec: PRSpec) -> List[str]:
        """
        Validates PR specification against Bible VI rules.
        Returns list of validation errors (empty if valid).
        """
        errors = []
        
        # Rule 1: Title format
        if not spec.title.startswith(self.TITLE_PREFIX):
            errors.append(f"PR title must start with '{self.TITLE_PREFIX}'")
            
        # Rule 2: Body must have required sections
        required_sections = [
            "## Summary",
            "## Implementation Details",
            "## Files Changed",
            "## Tests Run",
            "## Risks",
            "## Confidence Score"
        ]
        for section in required_sections:
            if section not in spec.body:
                errors.append(f"Missing required section: {section}")
                
        # Rule 3: Branch naming
        if not spec.head_branch.startswith("kita/"):
            errors.append("Head branch must start with 'kita/'")
            
        # Rule 4: Cannot target main directly without confirmation
        if spec.base_branch == "main":
            logger.warning("PR targeting main branch directly")
            
        return errors
    
    def format_pr_body(
        self, 
        summary: str,
        implementation_details: str,
        files_changed: List[str],
        tests_run: str,
        risks: str,
        confidence_score: float
    ) -> str:
        """
        Formats PR body according to Bible VI template.
        """
        files_list = "\n".join(f"- `{f}`" for f in files_changed)
        
        body = f"""## Summary
{summary}

## Implementation Details
{implementation_details}

## Files Changed
{files_list}

## Tests Run
{tests_run}

## Risks
{risks}

## Confidence Score
{confidence_score:.2f}/1.0

---
*This PR was created by [Kita.dev](https://kita.dev) - an autonomous coding agent.*
*Please review carefully before merging.*
"""
        return body
    
    def create_branch(self, repo_path: str, branch_name: str, base_ref: str = "HEAD") -> bool:
        """
        Creates a new branch from the given base reference.
        Uses git commands locally.
        """
        import subprocess
        
        try:
            # Create and checkout new branch
            subprocess.run(
                ["git", "checkout", "-b", branch_name, base_ref],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            logger.info(f"Created branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create branch: {e.stderr.decode() if e.stderr else str(e)}")
            return False
    
    def commit_changes(
        self, 
        repo_path: str, 
        files: List[FileChange], 
        commit_message: str
    ) -> bool:
        """
        Stages and commits file changes.
        """
        import subprocess
        
        try:
            # Write files
            for file_change in files:
                file_path = os.path.join(repo_path, file_change.path)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(file_change.content)
                    
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=repo_path,
                check=True,
                capture_output=True,
                env={**os.environ, "GIT_AUTHOR_NAME": "Kita Bot", "GIT_AUTHOR_EMAIL": "bot@kita.dev"}
            )
            
            logger.info(f"Committed changes: {commit_message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e.stderr.decode() if e.stderr else str(e)}")
            return False
    
    def push_branch(self, repo_path: str, branch_name: str, remote: str = "origin") -> bool:
        """
        Pushes branch to remote.
        """
        import subprocess
        
        try:
            subprocess.run(
                ["git", "push", "-u", remote, branch_name],
                cwd=repo_path,
                check=True,
                capture_output=True
            )
            logger.info(f"Pushed branch: {branch_name}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to push: {e.stderr.decode() if e.stderr else str(e)}")
            return False
    
    def create_pr_via_api(self, spec: PRSpec, repo_full_name: str) -> PRResult:
        """
        Creates PR via GitHub API.
        Requires authenticated client.
        """
        if not self.client:
            return PRResult(success=False, error="GitHub client not configured")
            
        # Validate spec
        errors = self.validate_pr_spec(spec)
        if errors:
            return PRResult(success=False, error=f"Validation errors: {errors}")
        
        try:
            # Real API Call
            logger.info(f"Creating PR: {spec.title} ({spec.head_branch} -> {spec.base_branch})")
            
            pr_number = self.client.create_pr(
                title=spec.title,
                body=spec.body,
                head=spec.head_branch,
                base=spec.base_branch,
                repo_full_name=repo_full_name
            )
            
            pr_url = f"https://github.com/{repo_full_name}/pull/{pr_number}"
            
            return PRResult(
                success=True,
                pr_number=pr_number,
                pr_url=pr_url
            )
        except Exception as e:
            return PRResult(success=False, error=str(e))
