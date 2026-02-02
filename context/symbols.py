"""
Symbol Extraction Module
Bible II, Section 3: Extract functions, classes. No semantic inference.
"""

import ast
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Symbol:
    name: str
    symbol_type: str  # 'function', 'class', 'method', 'variable'
    line_start: int
    line_end: int
    signature: str
    docstring: Optional[str] = None
    parent: Optional[str] = None


class SymbolExtractor:
    """
    Extracts symbols (functions, classes) from source files.
    Uses AST for Python - no semantic inference per Bible II.
    """

    def extract(self, content: str, file_path: str) -> List[Symbol]:
        """
        Extracts symbols from a file based on its type.
        """
        if file_path.endswith(".py"):
            return self._extract_python(content)
        elif file_path.endswith((".js", ".ts", ".jsx", ".tsx")):
            return self._extract_javascript(content)
        else:
            return []

    def _extract_python(self, content: str) -> List[Symbol]:
        """
        Extracts symbols from Python using AST.
        """
        symbols = []

        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            logger.warning(f"Failed to parse Python: {e}")
            return []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(
                node, ast.AsyncFunctionDef
            ):
                # Get signature
                args = []
                for arg in node.args.args:
                    arg_str = arg.arg
                    if arg.annotation:
                        arg_str += f": {ast.unparse(arg.annotation)}"
                    args.append(arg_str)

                returns = ""
                if node.returns:
                    returns = f" -> {ast.unparse(node.returns)}"

                signature = f"def {node.name}({', '.join(args)}){returns}"
                if isinstance(node, ast.AsyncFunctionDef):
                    signature = "async " + signature

                # Get docstring
                docstring = ast.get_docstring(node)

                # Determine parent class if method
                parent = None
                for potential_parent in ast.walk(tree):
                    if isinstance(potential_parent, ast.ClassDef):
                        for child in potential_parent.body:
                            if child is node:
                                parent = potential_parent.name
                                break

                symbols.append(
                    Symbol(
                        name=node.name,
                        symbol_type="method" if parent else "function",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        signature=signature,
                        docstring=docstring[:200] if docstring else None,
                        parent=parent,
                    )
                )

            elif isinstance(node, ast.ClassDef):
                # Get base classes
                bases = [ast.unparse(base) for base in node.bases]
                base_str = f"({', '.join(bases)})" if bases else ""

                signature = f"class {node.name}{base_str}"
                docstring = ast.get_docstring(node)

                symbols.append(
                    Symbol(
                        name=node.name,
                        symbol_type="class",
                        line_start=node.lineno,
                        line_end=node.end_lineno or node.lineno,
                        signature=signature,
                        docstring=docstring[:200] if docstring else None,
                    )
                )

        return symbols

    def _extract_javascript(self, content: str) -> List[Symbol]:
        """
        Extracts symbols from JavaScript/TypeScript using regex.
        (No external parser in V0 to minimize dependencies)
        """
        import re

        symbols = []
        lines = content.split("\n")

        # Function patterns
        func_patterns = [
            r"function\s+(\w+)\s*\((.*?)\)",  # function name(args)
            r"const\s+(\w+)\s*=\s*\((.*?)\)\s*=>",  # const name = (args) =>
            r"(\w+)\s*:\s*function\s*\((.*?)\)",  # name: function(args)
            r"async\s+function\s+(\w+)\s*\((.*?)\)",  # async function name(args)
        ]

        # Class pattern
        class_pattern = r"class\s+(\w+)(?:\s+extends\s+(\w+))?"

        for i, line in enumerate(lines, 1):
            # Check for functions
            for pattern in func_patterns:
                match = re.search(pattern, line)
                if match:
                    name = match.group(1)
                    args = match.group(2) if len(match.groups()) > 1 else ""
                    symbols.append(
                        Symbol(
                            name=name,
                            symbol_type="function",
                            line_start=i,
                            line_end=i,  # Can't determine end without parsing
                            signature=f"function {name}({args})",
                        )
                    )
                    break

            # Check for classes
            match = re.search(class_pattern, line)
            if match:
                name = match.group(1)
                extends = match.group(2) if match.group(2) else ""
                signature = f"class {name}" + (f" extends {extends}" if extends else "")
                symbols.append(
                    Symbol(
                        name=name,
                        symbol_type="class",
                        line_start=i,
                        line_end=i,
                        signature=signature,
                    )
                )

        return symbols

    def format_symbols(self, symbols: List[Symbol]) -> str:
        """
        Formats symbols into a readable string for context.
        """
        if not symbols:
            return "No symbols found."

        lines = ["Symbols:"]

        # Group by type
        classes = [s for s in symbols if s.symbol_type == "class"]
        functions = [s for s in symbols if s.symbol_type == "function"]
        methods = [s for s in symbols if s.symbol_type == "method"]

        if classes:
            lines.append("\nClasses:")
            for c in classes:
                lines.append(f"  L{c.line_start}: {c.signature}")
                if c.docstring:
                    lines.append(f'      "{c.docstring[:100]}..."')

        if functions:
            lines.append("\nFunctions:")
            for f in functions:
                lines.append(f"  L{f.line_start}: {f.signature}")

        if methods:
            lines.append("\nMethods:")
            for m in methods:
                lines.append(f"  L{m.line_start}: {m.parent}.{m.name}")

        return "\n".join(lines)
