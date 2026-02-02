"""
Context Selector Module
Bible II, Section 3: Select minimal file set, enforce token budget.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SelectedFile:
    path: str
    content: str
    token_estimate: int
    relevance_score: float


class ContextSelector:
    """
    Selects the minimal set of files needed for a task.
    Enforces token budget to prevent context overflow.
    """

    def __init__(self, token_budget: int = 50000):
        self.token_budget = token_budget
        # Rough estimate: 4 chars per token
        self.chars_per_token = 4

    def select(
        self, indexed_files: Dict[str, str], task: str, max_files: int = 20
    ) -> List[SelectedFile]:
        """
        Selects relevant files within token budget.

        Args:
            indexed_files: Dict of {path: content}
            task: The task description for relevance scoring
            max_files: Maximum number of files to include

        Returns:
            List of SelectedFile objects within budget
        """
        candidates = []

        for path, content in indexed_files.items():
            relevance = self._compute_relevance(path, content, task)
            token_estimate = len(content) // self.chars_per_token

            candidates.append(
                SelectedFile(
                    path=path,
                    content=content,
                    token_estimate=token_estimate,
                    relevance_score=relevance,
                )
            )

        # Sort by relevance (highest first)
        candidates.sort(key=lambda x: x.relevance_score, reverse=True)

        # Select within budget
        selected = []
        remaining_budget = self.token_budget

        for candidate in candidates[:max_files]:
            if candidate.token_estimate <= remaining_budget:
                selected.append(candidate)
                remaining_budget -= candidate.token_estimate
            else:
                # Try truncating content to fit
                available_chars = remaining_budget * self.chars_per_token
                if available_chars > 200:  # Minimum useful content
                    truncated = SelectedFile(
                        path=candidate.path,
                        content=candidate.content[:available_chars]
                        + "\n...[TRUNCATED]",
                        token_estimate=remaining_budget,
                        relevance_score=candidate.relevance_score,
                    )
                    selected.append(truncated)
                    remaining_budget = 0
                break

        logger.info(
            f"Selected {len(selected)} files within {self.token_budget} token budget"
        )
        return selected

    def _compute_relevance(self, path: str, content: str, task: str) -> float:
        """
        Computes relevance score for a file based on the task.
        Simple heuristic for V0 - can be enhanced with embeddings later.
        """
        score = 0.0
        task_lower = task.lower()
        path_lower = path.lower()
        content_lower = content.lower()

        # Extract keywords from task (simple tokenization)
        keywords = [w for w in task_lower.split() if len(w) > 3]

        # Path relevance
        for kw in keywords:
            if kw in path_lower:
                score += 0.3

        # Content relevance (first 1000 chars)
        sample = content_lower[:1000]
        for kw in keywords:
            if kw in sample:
                score += 0.1

        # File type bonuses
        if path.endswith(".py"):
            score += 0.1
        if "test" in path_lower:
            if "test" in task_lower:
                score += 0.2
            else:
                score -= 0.1  # Deprioritize tests unless task is about tests
        if "__init__" in path_lower:
            score -= 0.1  # Usually less relevant

        # Main files bonus
        if "main" in path_lower or "app" in path_lower:
            score += 0.15

        return min(1.0, max(0.0, score))

    def format_for_llm(self, selected: List[SelectedFile]) -> str:
        """
        Formats selected files into a context string for the LLM.
        """
        lines = ["Selected Repository Context:", "=" * 40]

        for f in selected:
            lines.append(f"\n[FILE: {f.path}] (relevance: {f.relevance_score:.2f})")
            lines.append("-" * 40)
            lines.append(f.content)

        total_tokens = sum(f.token_estimate for f in selected)
        lines.append(f"\n[Context: {len(selected)} files, ~{total_tokens} tokens]")

        return "\n".join(lines)
