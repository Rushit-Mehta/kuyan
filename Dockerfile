# KUYAN Dockerfile
# Builds a containerized version of the app

FROM python:3.11-slim

# Build arguments
ARG VERSION=unknown
ARG BUILD_DATE=unknown

# Set working directory
WORKDIR /app

# Add metadata labels
LABEL org.opencontainers.image.title="KUYAN"
LABEL org.opencontainers.image.description="Monthly Net Worth Tracker"
LABEL org.opencontainers.image.version="${VERSION}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.authors="Dhruv Chaudhary"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY database.py .
COPY currency.py .
COPY version.py .
COPY VERSION .
COPY create_sandbox_db.py .
COPY assets/ ./assets/

# Create data directory for database persistence
RUN mkdir -p /app/data

# Create sandbox database with sample data
RUN python3 create_sandbox_db.py

# Expose Streamlit default port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false", \
     "--server.fileWatcherType=none"]
