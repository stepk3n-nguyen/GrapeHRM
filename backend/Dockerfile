FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for PyMySQL + cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Flask default port
EXPOSE 5000

# Run with hot-reload in development
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000", "--reload"]
