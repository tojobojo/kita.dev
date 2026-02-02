"""
Context Summarizer Module
Bible II, Section 3: Compress content deterministically.
"""

import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class ContextSummarizer:
    """
    Compresses file content deterministically to reduce token usage.
    No embeddings in V0 - uses rule-based compression.
    """

    def __init__(self, max_lines_per_file: int = 100):
        self.max_lines_per_file = max_lines_per_file

    def summarize(self, content: str, file_path: str) -> str:
        """
        Summarizes file content based on file type.

        Args:
            content: Raw file content
            file_path: Path to determine file type

        Returns:
            Compressed/summarized content
        """
        if file_path.endswith(".py"):
            return self._summarize_python(content)
        elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            return self._summarize_javascript(content)
        elif file_path.endswith(".md"):
            return self._summarize_markdown(content)
        elif file_path.endswith((".json", ".yaml", ".yml")):
            return self._summarize_config(content)
        else:
            return self._summarize_generic(content)

    def _summarize_python(self, content: str) -> str:
        """
        Summarizes Python files by keeping:
        - Imports
        - Class/function signatures
        - Docstrings
        - First few lines of each function
        """
        lines = content.split("\n")
        summary_lines = []
        in_docstring = False
        docstring_char = None

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Track docstrings
            if '"""' in stripped or "'''" in stripped:
                quote = '"""' if '"""' in stripped else "'''"
                count = stripped.count(quote)
                if count == 2:
                    summary_lines.append(line)
                    continue
                elif count == 1:
                    in_docstring = not in_docstring
                    docstring_char = quote if in_docstring else None

            # Keep important lines
            if (
                stripped.startswith("import ")
                or stripped.startswith("from ")
                or stripped.startswith("class ")
                or stripped.startswith("def ")
                or stripped.startswith("@")  # Decorators
                or in_docstring
                or i < 10
            ):  # Keep first 10 lines
                summary_lines.append(line)
            elif len(summary_lines) < self.max_lines_per_file:
                # Keep some body lines
                if stripped and not stripped.startswith("#"):
                    summary_lines.append(line)

        if len(lines) > len(summary_lines):
            summary_lines.append(
                f"\n# ... [{len(lines) - len(summary_lines)} lines omitted]"
            )

        return "\n".join(summary_lines)

    def _summarize_javascript(self, content: str) -> str:
        """
        Summarizes JS/TS files by keeping:
        - Imports/exports
        - Function/class declarations
        - Type definitions
        """
        lines = content.split("\n")
        summary_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if (
                stripped.startswith("import ")
                or stripped.startswith("export ")
                or stripped.startswith("const ")
                or stripped.startswith("function ")
                or stripped.startswith("class ")
                or stripped.startswith("interface ")
                or stripped.startswith("type ")
                or "async function" in stripped
                or "=>" in stripped[:50]  # Arrow functions
                or i < 10
            ):
                summary_lines.append(line)
            elif len(summary_lines) < self.max_lines_per_file:
                if stripped and not stripped.startswith("//"):
                    summary_lines.append(line)

        if len(lines) > len(summary_lines):
            summary_lines.append(
                f"\n// ... [{len(lines) - len(summary_lines)} lines omitted]"
            )

        return "\n".join(summary_lines)

    def _summarize_markdown(self, content: str) -> str:
        """
        Summarizes Markdown by keeping headers and first paragraph.
        """
        lines = content.split("\n")
        summary_lines = []

        for line in lines:
            if line.startswith("#") or len(summary_lines) < 30:
                summary_lines.append(line)

        if len(lines) > len(summary_lines):
            summary_lines.append(
                f"\n... [{len(lines) - len(summary_lines)} lines omitted]"
            )

        return "\n".join(summary_lines)

    def _summarize_config(self, content: str) -> str:
        """
        Keeps config files mostly intact (usually important).
        """
        lines = content.split("\n")
        if len(lines) <= self.max_lines_per_file:
            return content
        return (
            "\n".join(lines[: self.max_lines_per_file])
            + f"\n... [{len(lines) - self.max_lines_per_file} lines omitted]"
        )

    def _summarize_generic(self, content: str) -> str:
        """
        Generic summarization - keep first N lines.
        """
        lines = content.split("\n")
        max_lines = min(50, self.max_lines_per_file)

        if len(lines) <= max_lines:
            return content
        return (
            "\n".join(lines[:max_lines])
            + f"\n... [{len(lines) - max_lines} lines omitted]"
        )

    def batch_summarize(self, files: Dict[str, str]) -> Dict[str, str]:
        """
        Summarizes multiple files.
        """
        return {path: self.summarize(content, path) for path, content in files.items()}
