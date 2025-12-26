#!/bin/bash

# KUYAN Docker Stop Script

echo "Stopping KUYAN..."

docker compose down

if [ $? -eq 0 ]; then
    echo "✅ KUYAN stopped successfully"
else
    echo "❌ Failed to stop KUYAN"
    exit 1
fi
