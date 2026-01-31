# Secure Sandbox Environment for Kita.dev
# Bible V, Section 3: Sandbox Requirements

# Base image: Lightweight Python
FROM python:3.10-slim

# Create a non-root user
# Bible V, Section 3: Non-root user
RUN useradd --create-home --shell /bin/bash sandbox_user

# Set working directory to user home
WORKDIR /home/sandbox_user

# Install basic dependencies (only those allowed)
# Bible V, Section 6: Allowed: Language runtimes, Test runners, Linters
RUN pip install --no-cache-dir pytest pylint

# Create a strictly designated workspace directory
RUN mkdir -p /workspace && chown sandbox_user:sandbox_user /workspace

# Switch to non-root user
USER sandbox_user

# Set workspace as working directory
WORKDIR /workspace

# Container must be run with --read-only and --network none by the executor.
# This Dockerfile provides the image structure.

# Entrypoint to keep container alive for execution commands or run directly
CMD ["/bin/bash"]
