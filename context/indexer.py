import os
from typing import List, Dict


class RepoIndexer:
    """
    Bible II, Section 3: Context Indexer
    Traverses repo tree and collects metadata and partial content.
    """

    def index(self, root_path: str) -> Dict[str, str]:
        """
        Walks the repository and returns a context string for the LLM.
        """
        context_lines = []
        context_lines.append(f"Repository Root: {root_path}")
        context_lines.append("Files:")

        ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            "venv",
            "env",
            ".venv",
            ".env",
            "dist",
            "build",
            "coverage",
        }
        for root, dirs, files in os.walk(root_path):
            dirs[:] = [
                d for d in dirs if d not in ignore_dirs and not d.startswith(".")
            ]

            for file in files:
                if file.startswith(".") or file.endswith(".pyc"):
                    continue

                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, root_path)

                context_lines.append(f"\n[FILE: {rel_path}]")

                # Check file size to avoid reading massive binaries
                if os.path.getsize(full_path) < 20000:  # 20KB limit for V0
                    try:
                        with open(
                            full_path, "r", encoding="utf-8", errors="ignore"
                        ) as f:
                            content = f.read()
                            # Truncate content for V0 context window management
                            if len(content) > 1000:
                                context_lines.append(
                                    content[:1000] + "\n...[TRUNCATED]"
                                )
                            else:
                                context_lines.append(content)
                    except Exception as e:
                        context_lines.append(f"[Error reading file: {e}]")
                else:
                    context_lines.append("[File too large, skipped content]")

        return "\n".join(context_lines)
