"""
Language Detection Module
Appendix F: Language Support & Execution Profiles
"""
import os
import logging
from typing import Optional, Tuple, Set
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)

@dataclass
class LanguageDetectionResult:
    primary_language: Optional[str]
    confidence: float
    supported: bool
    file_counts: dict
    reason: str

class LanguageDetector:
    """
    Detects the primary language of a repository.
    Per Appendix F, unsupported languages must trigger STOPPED_SAFE.
    """
    
    # Appendix F Section 1: Supported Languages (V0)
    PRIMARY_SUPPORTED: Set[str] = {"python"}
    SECONDARY_SUPPORTED: Set[str] = {"javascript", "typescript"}
    
    # File extension to language mapping
    EXTENSION_MAP = {
        '.py': 'python',
        '.pyw': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.mjs': 'javascript',
        '.cjs': 'javascript',
        '.java': 'java',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.go': 'go',
        '.rs': 'rust',
        '.c': 'c',
        '.h': 'c',
        '.cpp': 'cpp',
        '.hpp': 'cpp',
        '.cc': 'cpp',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.sh': 'shell',
        '.bash': 'shell',
    }
    
    # Files that indicate language (package managers, configs)
    INDICATOR_FILES = {
        'requirements.txt': 'python',
        'pyproject.toml': 'python',
        'setup.py': 'python',
        'Pipfile': 'python',
        'package.json': 'javascript',
        'tsconfig.json': 'typescript',
        'pom.xml': 'java',
        'build.gradle': 'java',
        'Cargo.toml': 'rust',
        'go.mod': 'go',
        'Gemfile': 'ruby',
        'composer.json': 'php',
    }
    
    def detect(self, repo_path: str) -> LanguageDetectionResult:
        """
        Detects the primary language of a repository.
        
        Args:
            repo_path: Path to the repository root
            
        Returns:
            LanguageDetectionResult with detection info
        """
        file_counts = Counter()
        indicator_matches = []
        
        ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', 'env', 
                       '.venv', '.env', 'dist', 'build', 'vendor'}
        
        # Walk repository
        for root, dirs, files in os.walk(repo_path):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
            
            for file in files:
                # Check indicator files
                if file in self.INDICATOR_FILES:
                    indicator_matches.append(self.INDICATOR_FILES[file])
                
                # Count by extension
                _, ext = os.path.splitext(file)
                if ext in self.EXTENSION_MAP:
                    file_counts[self.EXTENSION_MAP[ext]] += 1
        
        # Determine primary language
        primary_language = None
        confidence = 0.0
        
        # Prioritize indicator files
        if indicator_matches:
            # Most common indicator
            indicator_counter = Counter(indicator_matches)
            primary_language = indicator_counter.most_common(1)[0][0]
            confidence = 0.9
        elif file_counts:
            # Most common file type
            primary_language, count = file_counts.most_common(1)[0]
            total_files = sum(file_counts.values())
            confidence = count / total_files if total_files > 0 else 0.0
        
        # Check if supported
        all_supported = self.PRIMARY_SUPPORTED | self.SECONDARY_SUPPORTED
        supported = primary_language in all_supported if primary_language else False
        
        # Build reason
        if not primary_language:
            reason = "Could not determine primary language. No recognizable source files found."
            supported = False
        elif supported:
            reason = f"Primary language '{primary_language}' is supported."
        else:
            reason = f"Primary language '{primary_language}' is NOT supported in V0. Supported: {', '.join(all_supported)}."
        
        result = LanguageDetectionResult(
            primary_language=primary_language,
            confidence=confidence,
            supported=supported,
            file_counts=dict(file_counts),
            reason=reason
        )
        
        logger.info(f"Language detection: {primary_language} (confidence: {confidence:.2f}, supported: {supported})")
        return result
    
    def get_execution_profile(self, language: str) -> Optional[dict]:
        """
        Returns the execution profile for a supported language.
        Per Appendix F Section 4.
        """
        profiles = {
            'python': {
                'runtime': 'python3',
                'test_commands': ['pytest', 'python -m unittest'],
                'lint_commands': ['pylint', 'flake8', 'mypy'],
                'package_manager': 'pip',
            },
            'javascript': {
                'runtime': 'node',
                'test_commands': ['npm test', 'yarn test', 'pnpm test'],
                'lint_commands': ['eslint'],
                'package_manager': 'npm',
            },
            'typescript': {
                'runtime': 'node',
                'test_commands': ['npm test', 'yarn test', 'pnpm test'],
                'lint_commands': ['eslint', 'tsc --noEmit'],
                'package_manager': 'npm',
            },
        }
        return profiles.get(language)
