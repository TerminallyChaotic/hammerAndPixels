#!/bin/bash
# One-click launcher for CT LLC Scraper
# Usage: ./start.sh

set -e

echo "======================================"
echo "  CT LLC Scraper - Hammer & Pixels"
echo "======================================"
echo ""

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed."
    echo "Install Docker Desktop from https://docker.com/get-started"
    exit 1
fi

# Check if docker compose is available (v2 plugin or standalone)
if docker compose version &> /dev/null; then
    COMPOSE="docker compose"
elif command -v docker-compose &> /dev/null; then
    COMPOSE="docker-compose"
else
    echo "Error: Docker Compose is not installed."
    exit 1
fi

echo "Building and starting container..."
echo ""
$COMPOSE up --build -d

echo ""
echo "======================================"
echo "  LLC Scraper is running!"
echo ""
echo "  Dashboard: http://localhost:5001"
echo ""
echo "  Commands:"
echo "    Stop:    $COMPOSE down"
echo "    Logs:    $COMPOSE logs -f"
echo "    Rebuild: $COMPOSE up --build -d"
echo "======================================"
