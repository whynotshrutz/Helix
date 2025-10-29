# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Agno with all optional dependencies
RUN pip install --no-cache-dir "agno[all]>=2.0.0"

# Copy the entire project
COPY . .

# Install the helix package
RUN pip install -e .

# Expose the server port
EXPOSE 7777

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HELIX_LOG_LEVEL=INFO

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7777/health || exit 1

# Run the server
CMD ["python", "-m", "helix", "--serve"]
