#!/bin/bash

# KUYAN Docker Build Script with Versioning (No Cache)

# Read version from VERSION file
VERSION=$(cat VERSION 2>/dev/null || echo "unknown")
BUILD_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "Building KUYAN Docker image (NO CACHE)..."
echo "Version: $VERSION"
echo "Build Date: $BUILD_DATE"
echo ""

# Stop any running containers
echo "Stopping containers..."
docker compose down > /dev/null 2>&1

# Delete all kuyan images
echo "Deleting existing kuyan images..."
docker rmi kuyan:latest kuyan:$VERSION > /dev/null 2>&1
docker images | grep kuyan | awk '{print $3}' | xargs -r docker rmi -f > /dev/null 2>&1

# Clear Docker build cache
echo "Clearing Docker build cache..."
docker builder prune -af > /dev/null 2>&1

# Prune all unused images
echo "Pruning unused images..."
docker image prune -af > /dev/null 2>&1

# Export for docker-compose
export VERSION
export BUILD_DATE

# Build the image with --no-cache flag
docker compose build --no-cache

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "Image: kuyan:$VERSION"
    echo "Also tagged as: kuyan:latest"
    echo ""
    echo "To run: docker compose up -d"
else
    echo ""
    echo "❌ Build failed!"
    exit 1
fi
