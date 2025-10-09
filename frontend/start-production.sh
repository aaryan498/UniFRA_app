#!/bin/bash
# Production server startup script for UniFRA Frontend
# This script ensures the production build exists and starts the Express server

cd /app/frontend

# Check if production build exists
if [ ! -d "build" ] || [ ! -f "build/index.html" ]; then
    echo "Production build not found. Building now..."
    NODE_OPTIONS="--max-old-space-size=4096" yarn build
fi

# Start the production server
echo "Starting UniFRA Frontend Production Server..."
exec node server.js
