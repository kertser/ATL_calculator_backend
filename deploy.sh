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
    git pull origin master  # Fixed: changed from 'main' to 'master'
else
    echo "Cloning repository..."
    git clone https://github.com/kertser/ATL_calculator_backend.git .
fi

# Deploy with docker-compose
echo "Deploying with Docker Compose..."
docker-compose down --remove-orphans || true  # Stop existing containers
docker-compose build --no-cache              # Rebuild image
docker-compose up -d                          # Start containers

# Wait for container to be ready
echo "Waiting for container to start..."
sleep 5

# Test if container is running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Container is running successfully"

    # Test API health
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ API health check passed"
    else
        echo "❌ API health check failed"
        docker-compose logs
        exit 1
    fi
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
