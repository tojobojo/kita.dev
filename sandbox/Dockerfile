# Secure Sandbox Environment for Kita.dev
# Bible V, Section 3: Sandbox Requirements

# Base image: Python with Node.js
FROM python:3.11-slim

# Create a non-root user
# Bible V, Section 3: Non-root user
RUN useradd --create-home --shell /bin/bash sandbox_user

# Set working directory to user home
WORKDIR /home/sandbox_user

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS for JavaScript/TypeScript support
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Python testing and linting tools
# Bible V, Section 6: Allowed: Language runtimes, Test runners, Linters
RUN pip install --no-cache-dir pytest pylint black mypy

# Install Node.js testing tools
RUN npm install -g jest eslint prettier typescript ts-node

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

