#!/bin/bash

set -e

echo "================================================"
echo "  AI Documents Assistant - Initial Setup"
echo "  Optimized for Apple Silicon M4 Max"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo "ℹ️  $1"
}

# Detect OS and Architecture
echo ""
echo "🔍 Detecting system information..."
OS=$(uname -s)
ARCH=$(uname -m)

print_info "Operating System: $OS"
print_info "Architecture: $ARCH"

if [[ "$OS" != "Darwin" ]]; then
    print_warning "This setup script is optimized for macOS. You may need to adjust settings."
fi

if [[ "$ARCH" == "arm64" ]]; then
    print_success "Apple Silicon detected (M1/M2/M3/M4)"
else
    print_warning "Not running on Apple Silicon. GPU acceleration may differ."
fi

# Check prerequisites
echo ""
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed."
    echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
print_success "Docker found: $(docker --version)"

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker Desktop."
    exit 1
fi
print_success "Docker is running"

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available."
    echo "   Docker Desktop should include Docker Compose. Please update Docker Desktop."
    exit 1
fi
print_success "Docker Compose found: $(docker compose version)"

# Check available disk space
echo ""
echo "💾 Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
print_info "Available disk space: $AVAILABLE_SPACE"
print_warning "Recommended: 30GB+ free space for models and data"

# Check available memory
echo ""
echo "🧠 Checking system memory..."
if [[ "$OS" == "Darwin" ]]; then
    TOTAL_RAM=$(sysctl -n hw.memsize | awk '{print $0/1024/1024/1024 " GB"}')
    print_info "Total RAM: $TOTAL_RAM"
    print_warning "Recommended: 16GB+ RAM (32GB for best performance)"
fi

# Create directory structure
echo ""
echo "📁 Creating directory structure..."

# Create keycloak directory
if [ ! -d "keycloak" ]; then
    mkdir -p keycloak/themes
    print_success "Created keycloak directory"
else
    print_info "keycloak directory already exists"
fi

# Create backend directories
if [ ! -d "backend/app" ]; then
    mkdir -p backend/app/{api/routes,core,services,models}
    touch backend/app/__init__.py
    touch backend/app/api/__init__.py
    touch backend/app/api/routes/__init__.py
    touch backend/app/core/__init__.py
    touch backend/app/services/__init__.py
    touch backend/app/models/__init__.py
    print_success "Created backend directory structure"
else
    print_info "backend directory structure already exists"
fi

# Create frontend directories
if [ ! -d "frontend/src" ]; then
    mkdir -p frontend/src/{app,assets,environments}
    print_success "Created frontend directory structure"
else
    print_info "frontend directory structure already exists"
fi

# Create uploads directory
if [ ! -d "backend/app/uploads" ]; then
    mkdir -p backend/app/uploads
    print_success "Created uploads directory"
else
    print_info "uploads directory already exists"
fi

# Create .env file
echo ""
echo "📝 Creating environment configuration..."

if [ -f .env ]; then
    print_warning ".env file already exists. Backing up to .env.backup"
    cp .env .env.backup
fi

cat > .env << 'EOF'
# Keycloak Configuration
KEYCLOAK_URL=http://localhost:8080
KEYCLOAK_REALM=ai-docs-assistant
KEYCLOAK_CLIENT_ID=ai-docs-client
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=admin123

# Backend Configuration
BACKEND_URL=http://localhost:8000
API_CORS_ORIGINS=http://localhost:4200

# Qdrant Configuration
QDRANT_HOST=qdrant
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# LLM Configuration (Ollama) - Optimized for Apple Silicon M4 Max
OLLAMA_HOST=http://ollama:11434
OLLAMA_MODEL=phi3:mini
EMBEDDING_MODEL=BAAI/bge-base-en-v1.5
MAX_TOKENS=2048
TEMPERATURE=0.7

# Postgres (for Keycloak)
POSTGRES_DB=keycloak
POSTGRES_USER=keycloak
POSTGRES_PASSWORD=keycloak123
EOF

print_success "Created .env file"

# Create .gitignore if it doesn't exist
echo ""
echo "📝 Creating .gitignore..."

if [ ! -f .gitignore ]; then
    cat > .gitignore << 'EOF'
# Environment
.env
.env.local
.env.backup
*.backup

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
.venv

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.angular/
dist/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Docker
.dockerignore

# Uploads
backend/app/uploads/*
!backend/app/uploads/.gitkeep

# Logs
*.log
logs/
EOF
    print_success "Created .gitignore"
else
    print_info ".gitignore already exists"
fi

# Make scripts executable
echo ""
echo "🔧 Making scripts executable..."

chmod +x *.sh 2>/dev/null || true
print_success "Scripts are now executable"

# Verify required files
echo ""
echo "🔍 Verifying required files..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "start.sh"
    "stop.sh"
    ".env"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
        print_error "Missing: $file"
    else
        print_success "Found: $file"
    fi
done

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    print_error "Some required files are missing!"
    echo "Please ensure all files are present before running ./start.sh"
    exit 1
fi

# Docker configuration check
echo ""
echo "🐳 Checking Docker configuration..."

# Check Docker resources
if [[ "$OS" == "Darwin" ]]; then
    print_info "Docker Desktop Resource Settings:"
    echo "   Please ensure in Docker Desktop → Settings → Resources:"
    echo "   - CPUs: 8-10 cores (recommended)"
    echo "   - Memory: 12-16 GB (recommended)"
    echo "   - Swap: 2 GB"
    echo "   - Disk size: 60 GB"
fi

# Summary
echo ""
echo "================================================"
echo "  ✅ Setup Complete!"
echo "================================================"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Review and update .env file if needed:"
echo "   nano .env"
echo ""
echo "2. Ensure Docker Desktop has sufficient resources:"
echo "   Docker Desktop → Settings → Resources"
echo ""
echo "3. Start the system:"
echo "   ./start.sh"
echo ""
echo "4. Access the application:"
echo "   http://localhost:4200"
echo ""
echo "5. Login with demo credentials:"
echo "   Username: demo"
echo "   Password: demo123"
echo ""
echo "================================================"
echo ""
echo "💡 Useful Commands:"
echo ""
echo "   ./start.sh         - Start all services"
echo "   ./stop.sh          - Stop all services"
echo "   ./ollama-models.sh - Manage AI models"
echo ""
echo "📚 Documentation:"
echo "   README.md          - Full documentation"
echo "   README-MAC.md      - Mac-specific guide"
echo ""
echo "🆘 Troubleshooting:"
echo "   docker compose logs -f          - View all logs"
echo "   docker compose ps               - Check service status"
echo "   docker compose restart backend  - Restart a service"
echo ""
echo "================================================"
echo ""
echo "System Information Summary:"
echo "  OS: $OS ($ARCH)"
echo "  Docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"
echo "  Disk Space: $AVAILABLE_SPACE available"
if [[ "$OS" == "Darwin" ]]; then
    echo "  RAM: $TOTAL_RAM"
fi
echo ""
echo "Ready to start! Run: ./start.sh"
echo ""