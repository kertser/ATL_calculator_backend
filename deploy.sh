#!/bin/bash

# UV Calculator Backend Deployment/Update Script
set -e  # Exit on any error

echo "Starting UV Calculator Backend deployment/update..."

# Define deployment directory
DEPLOY_DIR="Projects/Calculator/server"

# Create deployment directory if it doesn't exist
echo "Setting up deployment directory: $DEPLOY_DIR"
sudo mkdir -p "$DEPLOY_DIR"
sudo chown $USER:$USER "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

# Handle git repository
if [ -d ".git" ]; then
    echo "Updating existing repository..."
    git pull origin master
else
    echo "Cloning repository..."
    git clone https://github.com/kertser/ATL_calculator_backend.git .
fi

# Deploy with docker-compose
echo "Deploying with Docker Compose..."
docker-compose down --remove-orphans || true  # Stop existing containers
docker-compose build --no-cache              # Rebuild image
docker-compose up -d                          # Start containers

# Wait for container to be ready with retry logic
echo "Waiting for container to start..."
sleep 10  # Initial wait for container startup

# Test if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running successfully"

    # Test API health with retries
    echo "Testing API health (may take up to 30 seconds)..."
    for i in {1..6}; do
        if curl -f -s http://localhost:5000/health > /dev/null 2>&1; then
            echo "✅ API health check passed"
            break
        else
            if [ $i -eq 6 ]; then
                echo "❌ API health check failed after 30 seconds"
                docker-compose logs --tail=20
                exit 1
            else
                echo "⏳ API not ready yet, waiting 5 more seconds... (attempt $i/6)"
                sleep 5
            fi
        fi
    done
else
    echo "❌ Container failed to start"
    docker-compose logs
    exit 1
fi

# Check nginx configuration and reload
echo "Checking nginx configuration..."
if sudo nginx -t; then
    echo "✅ Nginx configuration is valid"
    sudo systemctl reload nginx
    echo "✅ Nginx reloaded successfully"
else
    echo "❌ Nginx configuration has errors"
    exit 1
fi

echo "🎉 Deployment/Update completed successfully!"
echo "API is accessible at: http://212.235.125.206/api/"
echo "Frontend is accessible at: http://212.235.125.206:9876"
