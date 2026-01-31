from typing import Set

"""
Bible V, Section 6: Command Allowlist
Explicit definition of what is allowed and what is forbidden.
"""

# Commands explicitly allowed in the sandbox
# This list is MINIMAL.
COMMAND_ALLOWLIST: Set[str] = {
    # Python
    "python", "python3", "pip", "pytest", "pylint",
    
    # Node/JS (if we support it later, keeping for now as per V0 spec allows JS)
    "node", "npm", "yarn", "pnpm", "eslint",
    
    # Basic utilities
    "ls", "dir", "cat", "echo", "grep", "find", "wc", "head", "tail", "pwd",
    "mkdir", "rm", "cp", "mv", "touch", "chmod", "date"
}

# Commands explicitly forbidden (for fast-fail, though undefined commands are also blocked)
FORBIDDEN_COMMANDS: Set[str] = {
    "curl", "wget", "scp", "ssh", "ftp", "telnet", "nc", "ncat",  # Network
    "sudo", "su",  # Privilege
    "apt", "apt-get", "yum", "apk", "dnf",  # System packages
    "docker", "podman", "kubectl",  # Orchestration
    "reboot", "shutdown", "init"  # System control
}

def is_command_allowed(command_line: str) -> bool:
    """
    Checks if a command line starts with an allowed executable.
    Does NOT support chaining (&&, ||, |) in V0 for safety.
    """
    if not command_line or not command_line.strip():
        return False
        
    parts = command_line.strip().split()
    if not parts:
        return False
    
    executable = parts[0]
    
    # 1. Check strict equality against allowlist
    # We might allow absolute paths /usr/bin/python later, but for now strict.
    if executable not in COMMAND_ALLOWLIST:
        return False

    # 2. Check explicitly forbidden tokens anywhere in args (simple heuristic)
    for token in parts:
        if token in FORBIDDEN_COMMANDS:
            return False

    # 3. Check for shell chaining operators (Forbidden in V0 for simplicity)
    # Bible V Section 6 forbid "shell chaining"
    forbidden_chars = [";", "&&", "||", "|", "`", "$("]
    if any(char in command_line for char in forbidden_chars):
         return False

    return True
