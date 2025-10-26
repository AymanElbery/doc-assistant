#!/bin/bash

set -e

echo "================================================"
echo "  AI Documents Assistant - Stopping System"
echo "================================================"

echo ""
echo "🛑 Stopping all services..."
docker compose down

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "📝 Notes:"
echo "   - Data volumes are preserved"
echo "   - To remove all data: docker compose down -v"
echo "   - To restart: ./start.sh"
echo ""