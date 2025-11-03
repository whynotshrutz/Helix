# Production Dockerfile for Secure Code Execution Sandbox
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install basic tools and security packages
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install common Python packages for code execution
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    numpy \
    pandas \
    requests \
    matplotlib

# Create non-root user for code execution
RUN useradd -m -s /bin/bash -u 2000 sandbox && \
    mkdir -p /workspace /home/sandbox && \
    chown -R sandbox:sandbox /workspace /home/sandbox

# Copy executor script
COPY executor.py /home/sandbox/executor.py
RUN chown sandbox:sandbox /home/sandbox/executor.py

# Set resource limits and switch to non-root user
USER sandbox
WORKDIR /workspace

# Expose port for executor service
EXPOSE 8888

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

CMD ["python", "/home/sandbox/executor.py"]
