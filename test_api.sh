#!/bin/bash

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="http://localhost:8080"

echo "======================================"
echo "Conveyor Belt API Test Suite"
echo "======================================"
echo ""

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}⚠ jq not installed. Output will not be formatted.${NC}"
    echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    JQ_CMD="cat"
else
    JQ_CMD="jq"
fi

# Function to test endpoint
test_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -e "${BLUE}Testing:${NC} $name"
    echo -e "${YELLOW}$method $endpoint${NC}"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✓ Success (HTTP $http_code)${NC}"
        echo "$body" | $JQ_CMD
    else
        echo -e "${RED}✗ Failed (HTTP $http_code)${NC}"
        echo "$body"
    fi
    
    echo ""
}

# 1. Health Check
test_endpoint "Health Check" "GET" "/health"

# 2. Root Endpoint
test_endpoint "API Info" "GET" "/"

# 3. Model Metrics
test_endpoint "Model Metrics" "GET" "/metrics"

# 4. MongoDB Record Count
test_endpoint "MongoDB Record Count" "GET" "/data/count"

# 5. Normal Reading
test_endpoint "Normal Reading Prediction" "POST" "/predict" '{
  "vibration": 0.8,
  "temperature": 30.0,
  "speed": 1.5,
  "actual_power": 2.0
}'

# 6. Anomaly Reading
test_endpoint "Anomaly Reading Prediction" "POST" "/predict" '{
  "vibration": 1.2,
  "temperature": 35.5,
  "speed": 1.5,
  "actual_power": 4.0
}'

# 7. Prediction without actual power
test_endpoint "Prediction Only (no anomaly check)" "POST" "/predict" '{
  "vibration": 0.9,
  "temperature": 31.0,
  "speed": 1.6
}'

# 8. Batch Prediction
test_endpoint "Batch Anomaly Detection" "POST" "/predict/batch" '{
  "readings": [
    {"Vibration": 0.8, "Temperature": 30.0, "Speed": 1.5, "PowerConsumption": 2.0},
    {"Vibration": 1.2, "Temperature": 35.5, "Speed": 1.5, "PowerConsumption": 4.0},
    {"Vibration": 0.9, "Temperature": 32.0, "Speed": 1.6, "PowerConsumption": 2.1}
  ]
}'

# 9. Reload Model
test_endpoint "Reload Model" "POST" "/model/reload"

echo "======================================"
echo -e "${GREEN}Test Suite Complete!${NC}"
echo "======================================"
echo ""
echo "API Documentation: ${BASE_URL}/docs"
echo ""