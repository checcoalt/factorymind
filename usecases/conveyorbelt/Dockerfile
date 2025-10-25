FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY usecases/conveyorbelt /app/usecases/conveyorbelt
COPY api_server.py /app/

# Create models directory
RUN mkdir -p /app/models

# Set Python to run in unbuffered mode
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "-u", "/app/api_server.py"]