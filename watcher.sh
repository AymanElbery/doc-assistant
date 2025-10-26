#!/bin/bash

set -e

echo "👀 Backend Watch with fswatch (Mac optimized)"
echo "=============================================="
echo ""

# Check if fswatch is installed
if ! command -v fswatch &> /dev/null; then
    echo "📦 fswatch not found. Installing..."
    brew install fswatch
fi

REBUILD_LOCK="/tmp/backend-rebuild.lock"

rebuild_backend() {
    # Prevent multiple simultaneous rebuilds
    if [ -f "$REBUILD_LOCK" ]; then
        echo "⏳ Rebuild already in progress, skipping..."
        return
    fi
    
    touch "$REBUILD_LOCK"
    
    echo ""
    echo "🔄 Changes detected at $(date '+%Y-%m-%d %H:%M:%S')"
    echo "📝 Changed file: $1"
    echo ""
    
    # Stop backend
    echo "🛑 Stopping backend..."
    docker compose stop backend
    docker compose rm -f backend
    
    # Rebuild (only backend, not dependencies)
    echo "🏗️ Rebuilding backend..."
    docker compose build backend
    
    # Start
    echo "🚀 Starting backend..."
    docker compose up -d backend
    
    # Wait for startup
    sleep 5
    
    # Show logs
    echo ""
    echo "📋 Recent logs:"
    docker compose logs --tail=30 backend
    
    echo ""
    echo "✅ Backend restarted successfully"
    echo "👀 Watching for changes..."
    echo ""
    
    rm "$REBUILD_LOCK"
}

export -f rebuild_backend

echo "👀 Watching backend/ for changes..."
echo "   - Python files (*.py)"
echo "   - Requirements (requirements.txt)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Watch for changes
fswatch -0 -r \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.pyo' \
    --exclude='.git' \
    --exclude='*.backup' \
    -e ".*" -i "\\.py$" -i "requirements\\.txt$" \
    backend/ | xargs -0 -n 1 -I {} bash -c 'rebuild_backend "$@"' _ {}