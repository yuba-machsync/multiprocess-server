FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY core/server.py core/client_simulator.py .
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd -m -u 1000 client && chown -R client:client /app
USER client

# Default command
CMD ["python", "client_simulator.py", "--host", "server", "--port", "8888", "--clients", "1", "--rate", "1000", "--duration", "60"]
