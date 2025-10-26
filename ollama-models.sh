#!/bin/bash

set -e

echo "================================================"
echo "  Ollama Model Management"
echo "  Optimized for Apple Silicon M4 Max"
echo "================================================"

# Check if Ollama container is running
if ! docker ps | grep -q ai-docs-ollama; then
    echo "❌ Ollama container is not running. Please start the system first with ./start.sh"
    exit 1
fi

case "$1" in
    list)
        echo ""
        echo "📋 Installed models:"
        docker exec ai-docs-ollama ollama list
        ;;
    
    pull)
        if [ -z "$2" ]; then
            echo "❌ Please specify a model name"
            echo "Usage: ./ollama-models.sh pull <model-name>"
            echo ""
            echo "🍎 Recommended models for Mac M4 Max (fast & efficient):"
            echo ""
            echo "  Ultra Fast (< 2GB):"
            echo "    • gemma2:2b (1.6GB) - Google's smallest, very fast"
            echo "    • qwen2.5:1.5b (1GB) - Alibaba's tiny model"
            echo ""
            echo "  Very Fast (2-3GB):"
            echo "    • phi3:mini (2.3GB) ⭐ DEFAULT - Microsoft's efficient model"
            echo "    • llama3.2:3b (2GB) - Meta's latest small model"
            echo "    • qwen2.5:3b (2.3GB) - Excellent multilingual"
            echo ""
            echo "  Fast (7-8GB):"
            echo "    • llama3.2:latest (4.7GB) - Best quality small model"
            echo "    • mistral:7b-instruct (4.1GB) - Popular choice"
            echo "    • gemma2:9b (5.4GB) - Google's mid-size"
            echo ""
            echo "  Advanced (14GB+) - Slower on Mac:"
            echo "    • llama3.1:latest (4.7GB) - Enhanced capabilities"
            echo "    • qwen2.5:14b (9GB) - Best quality"
            echo ""
            exit 1
        fi
        echo ""
        echo "📥 Pulling model: $2"
        docker exec ai-docs-ollama ollama pull "$2"
        echo "✅ Model pulled successfully!"
        echo ""
        echo "To use this model, update .env file:"
        echo "OLLAMA_MODEL=$2"
        echo "Then restart: ./stop.sh && ./start.sh"
        ;;
    
    rm|remove)
        if [ -z "$2" ]; then
            echo "❌ Please specify a model name"
            echo "Usage: ./ollama-models.sh rm <model-name>"
            exit 1
        fi
        echo ""
        echo "🗑️  Removing model: $2"
        docker exec ai-docs-ollama ollama rm "$2"
        echo "✅ Model removed successfully!"
        ;;
    
    info)
        if [ -z "$2" ]; then
            echo "❌ Please specify a model name"
            echo "Usage: ./ollama-models.sh info <model-name>"
            exit 1
        fi
        echo ""
        echo "ℹ️  Model information: $2"
        docker exec ai-docs-ollama ollama show "$2"
        ;;
    
    test)
        if [ -z "$2" ]; then
            echo "❌ Please specify a model name"
            echo "Usage: ./ollama-models.sh test <model-name>"
            exit 1
        fi
        echo ""
        echo "🧪 Testing model: $2"
        echo "   Prompt: 'Explain what RAG is in one sentence.'"
        docker exec -it ai-docs-ollama ollama run "$2" "Explain what RAG is in one sentence."
        ;;
    
    benchmark)
        if [ -z "$2" ]; then
            echo "❌ Please specify a model name"
            echo "Usage: ./ollama-models.sh benchmark <model-name>"
            exit 1
        fi
        echo ""
        echo "⚡ Benchmarking model: $2"
        echo "   Testing response speed on Apple Silicon..."
        
        START_TIME=$(date +%s)
        docker exec ai-docs-ollama ollama run "$2" "What is artificial intelligence?" > /dev/null
        END_TIME=$(date +%s)
        DURATION=$((END_TIME - START_TIME))
        
        echo "   ✅ Response time: ${DURATION}s"
        
        if [ $DURATION -lt 5 ]; then
            echo "   🚀 Performance: Excellent"
        elif [ $DURATION -lt 10 ]; then
            echo "   ⚡ Performance: Good"
        else
            echo "   🐌 Performance: Consider a smaller model"
        fi
        ;;
    
    recommended)
        echo ""
        echo "🍎 Recommended Setup for Mac M4 Max:"
        echo ""
        echo "For Daily Use (Best Balance):"
        echo "  $ ./ollama-models.sh pull phi3:mini"
        echo "  Size: 2.3GB | Speed: ⚡⚡⚡⚡⚡ | Quality: ⭐⭐⭐⭐"
        echo ""
        echo "For Maximum Speed:"
        echo "  $ ./ollama-models.sh pull gemma2:2b"
        echo "  Size: 1.6GB | Speed: ⚡⚡⚡⚡⚡ | Quality: ⭐⭐⭐"
        echo ""
        echo "For Best Quality (slower):"
        echo "  $ ./ollama-models.sh pull llama3.2:latest"
        echo "  Size: 4.7GB | Speed: ⚡⚡⚡ | Quality: ⭐⭐⭐⭐⭐"
        echo ""
        echo "For Multilingual:"
        echo "  $ ./ollama-models.sh pull qwen2.5:3b"
        echo "  Size: 2.3GB | Speed: ⚡⚡⚡⚡ | Quality: ⭐⭐⭐⭐"
        echo ""
        ;;
    
    *)
        echo ""
        echo "Usage: ./ollama-models.sh <command> [arguments]"
        echo ""
        echo "Commands:"
        echo "  list              - List all installed models"
        echo "  pull <model>      - Download a new model"
        echo "  rm <model>        - Remove a model"
        echo "  info <model>      - Show model information"
        echo "  test <model>      - Test a model with a simple prompt"
        echo "  benchmark <model> - Measure model response time"
        echo "  recommended       - Show recommended models for Mac M4 Max"
        echo ""
        echo "Examples:"
        echo "  ./ollama-models.sh list"
        echo "  ./ollama-models.sh pull phi3:mini"
        echo "  ./ollama-models.sh test phi3:mini"
        echo "  ./ollama-models.sh benchmark llama3.2:3b"
        echo "  ./ollama-models.sh recommended"
        echo ""
        ;;
esac