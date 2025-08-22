# Maya AI Telegram Bot - Production Dockerfile
# =============================================

# Use Python 3.10 slim image for optimal performance
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install system dependencies for better performance
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libx11-dev \
    libxrandr-dev \
    libxcursor-dev \
    libxinerama-dev \
    libxi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user for security
RUN groupadd -r maya && useradd -r -g maya maya
RUN chown -R maya:maya /app
USER maya

# Expose port for the Flask keep-alive server
EXPOSE 5000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Start the bot
CMD ["python", "main.py"]
