from dataclasses import dataclass

@dataclass
class ResourceLimits:
    """
    Defines hard limits for sandbox execution.
    Bible V, Section 5: Resource Limits
    Appendix D: Cost, Token & Compute Budget Law
    """
    # CPU quota (in seconds of CPU time allowed per run)
    cpu_seconds: int = 120
    
    # Wall-clock timeout (in seconds)
    timeout_seconds: int = 600  # 10 minutes
    
    # Memory limit (in bytes)
    memory_bytes: int = 2 * 1024 * 1024 * 1024  # 2 GB
    
    # Max output size to capture (to prevent OOM on massive logs)
    max_output_bytes: int = 10 * 1024 * 1024  # 10 MB

    @staticmethod
    def get_hard_ceilings() -> 'ResourceLimits':
        """
        Returns the absolute hard ceilings defined in Appendix D.
        These limits may NEVER be exceeded.
        """
        return ResourceLimits(
            cpu_seconds=300,        # 5 minutes CPU
            timeout_seconds=1200,   # 20 minutes Wall
            memory_bytes=4 * 1024 * 1024 * 1024, # 4 GB
            max_output_bytes=50 * 1024 * 1024    # 50 MB
        )

    def validate(self) -> None:
        """
        Validates that limits do not exceed hard ceilings.
        Raises ValueError if limits are unsafe.
        """
        hard = self.get_hard_ceilings()
        
        if self.cpu_seconds > hard.cpu_seconds:
            raise ValueError(f"CPU limit {self.cpu_seconds}s exceeds ceiling {hard.cpu_seconds}s")
        if self.timeout_seconds > hard.timeout_seconds:
            raise ValueError(f"Timeout {self.timeout_seconds}s exceeds ceiling {hard.timeout_seconds}s")
        if self.memory_bytes > hard.memory_bytes:
            raise ValueError(f"Memory limit {self.memory_bytes} bytes exceeds ceiling {hard.memory_bytes} bytes")
