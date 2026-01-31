from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class Command:
    trigger: str
    action: str
    args: Optional[str] = None

class CommandParser:
    """
    Bible VI, Section 2: Command Grammar
    Enforces strict, exact command matching.
    """
    
    # Strictly supported triggers
    VALID_COMMANDS = {
        "@kita implement this": "IMPLEMENT",
        "@kita retry": "RETRY",
        "@kita retry with constraints": "RETRY_CONSTRAINED",
        "@kita explain plan": "EXPLAIN",
        "@kita stop": "STOP"
    }

    def parse(self, comment_body: str) -> Optional[Command]:
        """
        Parses a comment for a valid command.
        Returns None if no *valid* command found.
        Strict matching: Case insensitive allowed, but grammar must be exact.
        """
        if not comment_body:
            return None
            
        cleaned = comment_body.strip().lower()
        
        # Check for strict matches
        for valid_cmd, action in self.VALID_COMMANDS.items():
            if cleaned == valid_cmd:
                return Command(trigger=valid_cmd, action=action)
            # Check for arguments if command supports it (e.g. constraints)
            # Bible VI says "Commands must be exact". 
            # "Natural language variants are invalid".
            # Does "@kita implement this <task>" exist?
            # Bible VI Section 2 list:
            # "@kita implement this"
            # "@kita retry"
            # ...
            # Usage implies the *issue context* is the task, or the comment contains args?
            # Phase 6 spec: "Support issue comment invocation only".
            # Usually users invoke on an existing issue.
            # Let's support strict command followed by optional text if strictly defined?
            # Bible VI says: "Only the following commands are valid".
            # It lists literals.
            # But "Rules: Commands must be exact".
            # Assumption: The *Issue Body* is the task, and the comment triggers it.
            # OR the comment IS the task? 
            # "Only the following commands are valid: @kita implement this".
            # This strongly implies the task is elsewhere (the strict literal triggers it).
            # If the user wants to give a NEW task in a comment, is that supported?
            # "Invalid commands -> clarification or STOP".
            # Let's implement strict literal matching first. 
            pass

        return None
