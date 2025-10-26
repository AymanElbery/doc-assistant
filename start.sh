#!/bin/bash

set -e

echo "================================================"
echo "  AI Documents Assistant - Starting System"
echo "  Optimized for Apple Silicon M4 Max"
echo "================================================"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update if needed."
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop and try again."
    exit 1
fi

# Detect platform
PLATFORM=$(uname -m)
OS=$(uname -s)

echo ""
echo "🖥️  System Information:"
echo "   OS: $OS"
echo "   Architecture: $PLATFORM"

if [[ "$OS" == "Darwin" ]]; then
    echo "   ✅ Running on macOS"
    if [[ "$PLATFORM" == "arm64" ]]; then
        echo "   ✅ Apple Silicon detected (M1/M2/M3/M4)"
    fi
fi

echo ""
echo "📦 Pulling required Docker images..."
docker compose pull

echo ""
echo "🏗️  Building custom images..."
docker compose build

echo ""
echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "⏳ Waiting for services to become healthy..."
echo "   This may take a few minutes..."

# Wait for services
max_wait=300  # 5 minutes
elapsed=0
interval=10

while [ $elapsed -lt $max_wait ]; do
    all_healthy=true
    for service in postgres keycloak qdrant ollama backend frontend; do
        if ! docker compose ps $service 2>/dev/null | grep -q "Up"; then
            all_healthy=false
            break
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        echo ""
        echo "✅ All services are running!"
        break
    fi
    
    echo "   Still waiting... (${elapsed}s elapsed)"
    sleep $interval
    elapsed=$((elapsed + interval))
done

if [ $elapsed -ge $max_wait ]; then
    echo ""
    echo "⚠️  Services are taking longer than expected to start."
    echo "   Check logs with: docker compose logs"
fi

echo ""
echo "📥 Pulling Ollama model: ${OLLAMA_MODEL:-phi3:mini}"
echo "   This will download ~2.3GB for Phi-3 Mini (first time only)..."
echo "   Optimized for Apple Silicon - fast and efficient!"

# Pull the Ollama model
docker exec ai-docs-ollama ollama pull ${OLLAMA_MODEL:-phi3:mini}

if [ $? -eq 0 ]; then
    echo "✅ Ollama model downloaded successfully!"
else
    echo "⚠️  Failed to pull Ollama model. You may need to pull it manually:"
    echo "   docker exec -it ai-docs-ollama ollama pull ${OLLAMA_MODEL:-phi3:mini}"
fi

echo ""
echo "================================================"
echo "  🎉 AI Documents Assistant is Ready!"
echo "================================================"
echo ""
echo "📍 Access URLs:"
echo "   Frontend:  http://localhost:4200"
echo "   Backend:   http://localhost:8000"
echo "   Backend API Docs: http://localhost:8000/docs"
echo "   Keycloak:  http://localhost:8080"
echo "   Qdrant:    http://localhost:6333/dashboard"
echo "   Ollama:    http://localhost:11434"
echo ""
echo "🤖 LLM Model: ${OLLAMA_MODEL:-phi3:mini}"
echo "   Size: 2.3GB"
echo "   Speed: Very Fast on Apple Silicon"
echo "   Quality: Excellent for its size"
echo ""
echo "🔐 Default Credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "📊 View logs:"
echo "   All services:     docker compose logs -f"
echo "   Specific service: docker compose logs -f [service-name]"
echo ""
echo "🤖 Ollama commands:"
echo "   List models:      docker exec ai-docs-ollama ollama list"
echo "   Pull model:       docker exec ai-docs-ollama ollama pull <model-name>"
echo "   Remove model:     docker exec ai-docs-ollama ollama rm <model-name>"
echo ""
echo "💡 Recommended models for Mac M4 Max:"
echo "   phi3:mini (2.3GB) - Default, very fast"
echo "   llama3.2:3b (2GB) - Newer, excellent quality"
echo "   qwen2.5:3b (2.3GB) - Great multilingual"
echo "   gemma2:2b (1.6GB) - Smallest, still good"
echo ""
echo "🛑 To stop the system:"
echo "   ./stop.sh"
echo ""
echo "================================================"