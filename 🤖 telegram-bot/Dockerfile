FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# NOTE: This is a long-polling worker with no HTTP server, so there is no
# endpoint to health-check. Container liveness is managed by the restart policy.

# Run the bot
CMD ["python", "bot.py"]
