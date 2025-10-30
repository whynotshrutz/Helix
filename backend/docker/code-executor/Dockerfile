# Dockerfile for secure code execution sandbox
FROM python:3.11-slim

# Install basic tools
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for code execution
RUN useradd -m -s /bin/bash sandbox && \
    mkdir -p /workspace && \
    chown sandbox:sandbox /workspace

# Set resource limits
USER sandbox
WORKDIR /workspace

# Copy executor script
COPY executor.py /home/sandbox/executor.py

# Expose port for executor service
EXPOSE 8888

CMD ["python", "/home/sandbox/executor.py"]
