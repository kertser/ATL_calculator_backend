#!/bin/bash
echo "=== UV Calculator Backend Status ==="
echo "Docker containers:"
docker-compose ps
echo ""
echo "Container logs (last 10 lines):"
docker-compose logs --tail=10
echo ""
echo "API Health Check:"
curl -s http://localhost:5000/health || echo "API not responding"
