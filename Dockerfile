# ============================================================
# SnapSave - Dockerfile
# ============================================================
FROM python:3.12-slim

# Install ffmpeg (required by yt-dlp for merging streams)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create temp download directory
RUN mkdir -p /tmp/snapsave

# Environment variables
ENV PORT=5000 \
    FLASK_DEBUG=0 \
    DOWNLOAD_DIR=/tmp/snapsave \
    PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run with gunicorn (4 workers, 120s timeout for large downloads)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "app:app"]