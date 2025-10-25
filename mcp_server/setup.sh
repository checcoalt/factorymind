#!/bin/bash

echo "======================================"
echo "Conveyor Belt Setup Script"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if directory structure exists
echo -e "${YELLOW}Checking directory structure...${NC}"

if [ ! -d "usecases/conveyorbelt" ]; then
    echo -e "${YELLOW}Creating directory structure...${NC}"
    mkdir -p usecases/conveyorbelt
    mkdir -p models
    echo -e "${GREEN}✓ Directories created${NC}"
else
    echo -e "${GREEN}✓ Directory structure exists${NC}"
fi

# Check required files
echo ""
echo -e "${YELLOW}Checking required files...${NC}"

REQUIRED_FILES=(
    "docker-compose.yml"
    "requirements.txt"
    "api_server.py"
    "usecases/conveyorbelt/Dockerfile"
    "usecases/conveyorbelt/regression.py"
    "usecases/conveyorbelt/training_data.json"
    "usecases/conveyorbelt/other_data.json"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file ${RED}(MISSING)${NC}"
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}Error: Missing required files!${NC}"
    echo "Please create the following files:"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All required files present${NC}"

# Check if Docker is running
echo ""
echo -e "${YELLOW}Checking Docker...${NC}"

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}⚠ docker-compose command not found, trying 'docker compose'${NC}"
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

echo -e "${GREEN}✓ Docker Compose available${NC}"

# Validate JSON files
echo ""
echo -e "${YELLOW}Validating JSON files...${NC}"

if command -v python3 &> /dev/null; then
    for json_file in usecases/conveyorbelt/*.json; do
        if python3 -c "import json; json.load(open('$json_file'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $(basename $json_file) is valid JSON"
        else
            echo -e "${RED}✗${NC} $(basename $json_file) is invalid JSON"
            exit 1
        fi
    done
else
    echo -e "${YELLOW}⚠ Python not found, skipping JSON validation${NC}"
fi

# Ask user to proceed
echo ""
echo -e "${YELLOW}Ready to build and start containers${NC}"
read -p "Do you want to continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled"
    exit 0
fi

# Build and start containers
echo ""
echo -e "${YELLOW}Building and starting containers...${NC}"
echo "This may take a few minutes on first run..."
echo ""

$DOCKER_COMPOSE up --build -d

# Wait for services to be healthy
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check if containers are running
if docker ps | grep -q conveyor_api_server; then
    echo -e "${GREEN}✓ API Server is running${NC}"
else
    echo -e "${RED}✗ API Server failed to start${NC}"
    echo "Check logs with: docker-compose logs api_server"
    exit 1
fi

if docker ps | grep -q conveyor_mongodb; then
    echo -e "${GREEN}✓ MongoDB is running${NC}"
else
    echo -e "${RED}✗ MongoDB failed to start${NC}"
    echo "Check logs with: docker-compose logs mongodb"
    exit 1
fi

# Test API endpoint
echo ""
echo -e "${YELLOW}Testing API endpoint...${NC}"
sleep 5

if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✓ API is responding${NC}"
else
    echo -e "${YELLOW}⚠ API not responding yet, it may still be initializing...${NC}"
    echo "Wait a moment and check: http://localhost:8000/docs"
fi

# Show summary
echo ""
echo "======================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "======================================"
echo ""
echo "Services running:"
echo "  • MongoDB:    http://localhost:27017"
echo "  • API Server: http://localhost:8000"
echo "  • API Docs:   http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo "  • View logs:     docker-compose logs -f"
echo "  • Stop all:      docker-compose down"
echo "  • Restart:       docker-compose restart"
echo "  • Check status:  docker-compose ps"
echo ""
echo "Test the API:"
echo "  curl http://localhost:8000/docs"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""