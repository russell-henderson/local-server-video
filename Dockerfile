FROM python:3.13-slim

# Install system dependencies including build tools
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    build-essential \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories
RUN mkdir -p videos images static/thumbnails logs

EXPOSE 5000

ENV FLASK_APP=main.py
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]