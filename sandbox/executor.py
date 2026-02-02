import subprocess
import logging
from dataclasses import dataclass
from typing import Optional, List
from sandbox.limits import ResourceLimits
from guardrails.rules import is_command_allowed
from guardrails.secrets import SecretDetector, SecurityError

logger = logging.getLogger(__name__)

@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False

class SecurityViolation(Exception):
    pass

class SandboxExecutor:
    """
    Executes commands within the Docker sandbox.
    Bible V Section 3, 4, 5.
    """
    
    IMAGE_NAME = "kita-sandbox:latest" # In real usage, this would be versioned
    CONTAINER_USER = "sandbox_user"

    def __init__(self):
        pass

    def run(self, command: str, repo_path: str, limits: ResourceLimits = ResourceLimits()) -> CommandResult:
        """
        Runs a command in the sandbox.
        ENFORCES:
        - Network isolation
        - Read-only root
        - Resource limits
        - Command allowlist
        - Secret scanning on output
        """
        
        from sandbox.docker_utils import ensure_sandbox_image
        
        # 0. Ensure Image
        ensure_sandbox_image(self.IMAGE_NAME)
        
        # 1. Validate Command
        if not is_command_allowed(command):
            logger.error(f"BLOCKED: Attempted unsafe command: {command}")
            raise SecurityViolation(f"Command not allowed: {command}")
            
        # 2. Validate Limits
        limits.validate() # Ensure below hard ceilings

        # 3. Construct Docker Command
        # Note: We use subprocess to call docker. In a real heavy system we might use docker-py, 
        # but subprocess is robust and dependency-free for V0.
        
        docker_cmd = [
            "docker", "run",
            "--rm",                      # Clean up after run
            "--network", "none",         # Bible V Section 4: Network Isolation
            "--read-only",               # Bible V Section 3: Read-only filesytem
            "--user", self.CONTAINER_USER,
            f"--cpus={limits.cpu_seconds / 60.0}", # Approx CPU quota (Docker --cpus is # of cores, --cpu-quota is hard. using cpus=limited is a simplifiction for V0)
                                                    # Actually, --cpus sets capacity. For strict time limit we use 'timeout' command externally or Popen timeout.
                                                    # Let's use Popen timeout for wall-clock.
            f"--memory={limits.memory_bytes}b",        # Bible V Section 5: Memory limit
            f"--memory={limits.memory_bytes}b",        # Bible V Section 5: Memory limit
            # Mount workspace (Volume handling would go here in real impl, assuming mapped)
             "-w", "/workspace",
             "-v", f"{repo_path}:/workspace", # Bind mount the repository
            self.IMAGE_NAME,
            "/bin/bash", "-c", command
        ]
        
        # Adjusting cpu arg interpretation: --cpus=1.0 means 1 core. limiting execution TIME is done via Popen.wait(timeout)
        # We'll just pass strict memory limits to docker.
        
        docker_cmd_clean = [arg for arg in docker_cmd if arg]

        logger.info(f"EXECUTING (SANDBOX): {command}")
        
        try:
            # 4. Execute with Timeout
            result = subprocess.run(
                docker_cmd_clean,
                capture_output=True,
                text=True,
                timeout=limits.timeout_seconds # Bible V Section 5: Wall-clock timeout
            )
            
            stdout = result.stdout
            stderr = result.stderr
            exit_code = result.returncode
            timed_out = False

        except subprocess.TimeoutExpired as e:
            logger.error("SANDBOX TIMEOUT")
            stdout = e.stdout.decode() if e.stdout else ""
            stderr = e.stderr.decode() if e.stderr else ""
            exit_code = -1
            timed_out = True
            
        # 5. Output Guardrails (Secrets)
        # Bible V Section 9: Secrets never exposed
        try:
            SecretDetector.validate_content_safe(stdout)
            SecretDetector.validate_content_safe(stderr)
        except SecurityError as se:
            logger.critical("SECRETS DETECTED IN OUTPUT. REDACTING AND FAILING.")
            # We fail the execution to be safe.
            return CommandResult(
                exit_code=-2,
                stdout="[REDACTED: SECURITY VIOLATION]",
                stderr="[REDACTED: SECRETS DETECTED IN OUTPUT]",
                timed_out=timed_out
            )

        return CommandResult(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out
        )
