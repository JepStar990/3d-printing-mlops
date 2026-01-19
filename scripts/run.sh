#!/bin/bash
# Quick start script for 3D Printer Monitoring
set -e

cd "$(dirname "$0")/.."

echo "Starting services..."
docker-compose up -d

echo ""
echo "Services started."
echo "- Grafana: http://localhost:3000 (admin/admin)"
echo "- InfluxDB UI: http://localhost:8086"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
