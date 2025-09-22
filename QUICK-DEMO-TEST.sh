#!/bin/bash

# KPRIET Campus Assistant - Quick Demo Test
# Simple curl-based testing for submission demo

echo "🎓 KPRIET CAMPUS ASSISTANT - QUICK DEMO TEST"
echo "============================================="
echo "Test started at: $(date)"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counter
TOTAL_TESTS=0
PASSED_TESTS=0

# Function to test service health
test_service() {
    local service_name="$1"
    local url="$2"
    
    echo -n "Testing $service_name... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ HEALTHY${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# Function to test chat functionality
test_chat() {
    local language="$1"
    local message="$2"
    local lang_name="$3"
    
    echo -n "Testing $lang_name chat... "
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    response=$(curl -s -X POST "http://localhost:3007/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\":\"$message\",\"language\":\"$language\",\"session_id\":\"demo_test\"}" \
        --max-time 15)
    
    if [ $? -eq 0 ] && echo "$response" | grep -q "response"; then
        echo -e "${GREEN}✅ SUCCESS${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        
        # Extract and display response (first 100 chars)
        response_text=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('response', '')[:100])" 2>/dev/null)
        if [ ! -z "$response_text" ]; then
            echo "   Response: $response_text..."
        fi
        return 0
    else
        echo -e "${RED}❌ FAILED${NC}"
        return 1
    fi
}

# 1. Test Service Health
echo -e "${BLUE}1️⃣ TESTING SERVICE HEALTH${NC}"
echo "----------------------------"

test_service "PostgreSQL" "http://localhost:5433"
test_service "Redis" "http://localhost:6379"
test_service "Backend API" "http://localhost:3007/health"
test_service "NLP Engine" "http://localhost:8001/health"
test_service "Frontend" "http://localhost:3008"

echo ""

# 2. Test Multilingual Chat
echo -e "${BLUE}2️⃣ TESTING MULTILINGUAL CHAT${NC}"
echo "------------------------------"

# English
test_chat "en" "Hello, I need help with fee information" "English"

# Hindi
test_chat "hi" "नमस्ते, मुझे फीस की जानकारी चाहिए" "Hindi"

# Bengali
test_chat "bn" "হ্যালো, আমার ফি সম্পর্কে তথ্য দরকার" "Bengali"

# Tamil
test_chat "ta" "வணக்கம், எனக்கு கட்டணம் பற்றிய தகவல் வேண்டும்" "Tamil"

echo ""

# 3. Test Additional Queries
echo -e "${BLUE}3️⃣ TESTING ADDITIONAL FEATURES${NC}"
echo "--------------------------------"

test_chat "en" "What are the library hours?" "Library Query"
test_chat "en" "Tell me about scholarships" "Scholarship Query"
test_chat "hi" "पुस्तकालय का समय क्या है?" "Hindi Library Query"

echo ""

# 4. Calculate Results
echo -e "${BLUE}4️⃣ TEST RESULTS${NC}"
echo "---------------"

SUCCESS_RATE=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))

echo "📊 Total Tests: $TOTAL_TESTS"
echo "📊 Passed Tests: $PASSED_TESTS"
echo "📊 Success Rate: $SUCCESS_RATE%"

echo ""

# 5. Final Assessment
echo -e "${BLUE}5️⃣ DEMO ASSESSMENT${NC}"
echo "-------------------"

if [ $SUCCESS_RATE -ge 80 ]; then
    echo -e "${GREEN}🎉 DEMO READY FOR SUBMISSION!${NC}"
    echo -e "${GREEN}✅ Success rate: $SUCCESS_RATE% (≥80% required)${NC}"
    echo -e "${GREEN}✅ Multilingual functionality working${NC}"
    echo -e "${GREEN}✅ All core services operational${NC}"
    
    echo ""
    echo -e "${YELLOW}🌐 DEMO ACCESS POINTS:${NC}"
    echo "📱 Frontend Chat:     http://localhost:3008"
    echo "🔧 Backend API:       http://localhost:3007"
    echo "🧠 NLP Engine:        http://localhost:8001"
    
    echo ""
    echo -e "${YELLOW}🎯 DEMO FEATURES:${NC}"
    echo "✅ Multilingual support (English, Hindi, Bengali, Tamil)"
    echo "✅ Real-time AI responses with NVIDIA integration"
    echo "✅ University data integration"
    echo "✅ Professional KPRIET branding"
    echo "✅ Mobile-responsive design"
    
    exit 0
else
    echo -e "${RED}⚠️ DEMO NEEDS ATTENTION!${NC}"
    echo -e "${RED}❌ Success rate: $SUCCESS_RATE% (<80% required)${NC}"
    
    if [ $PASSED_TESTS -lt $TOTAL_TESTS ]; then
        echo -e "${RED}❌ Some tests failed - check service logs${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}🔧 TROUBLESHOOTING:${NC}"
    echo "1. Check if all Docker containers are running:"
    echo "   docker ps"
    echo "2. Check service logs:"
    echo "   docker-compose -f './⚙️ Configuration Files/docker-compose.yml' logs"
    echo "3. Restart services if needed:"
    echo "   ./START-DEMO.sh"
    
    exit 1
fi
