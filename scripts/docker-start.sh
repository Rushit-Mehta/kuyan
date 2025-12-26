#!/bin/bash

# KUYAN Docker Start Script

echo "Starting KUYAN in Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

# Start container
docker compose up -d

# Wait for container to be healthy
echo "Waiting for container to start..."
sleep 3

# Check if container is running
if docker ps | grep -q kuyan; then
    echo ""
    echo "✅ KUYAN is running!"
    echo ""
    echo "Open your browser to: http://localhost:8501"
    echo ""
    echo "To view logs: docker compose logs -f"
    echo "To stop: docker compose down"
else
    echo ""
    echo "❌ Failed to start KUYAN"
    echo ""
    echo "Check logs with: docker compose logs"
    exit 1
fi
