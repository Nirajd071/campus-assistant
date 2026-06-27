#!/bin/bash

# 🎓 MULTILINGUAL CAMPUS AI - ONE-CLICK LAUNCHER
# Serves 12+ languages across India & Nepal with ZERO cost

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎓 MULTILINGUAL CAMPUS AI LAUNCHER${NC}"
echo "=================================="

# Check Docker
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# Detect the Compose command (v2 plugin "docker compose" or legacy "docker-compose")
if docker compose version >/dev/null 2>&1; then
    COMPOSE="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE="docker-compose"
else
    echo "❌ Docker Compose not found. Install the Docker Compose plugin or docker-compose."
    exit 1
fi

COMPOSE_FILE="./⚙️ Configuration Files/docker-compose.yml"

# Main function
case "${1:-menu}" in
    "start")
        echo "🚀 Starting all services..."
        $COMPOSE -f "$COMPOSE_FILE" down 2>/dev/null || true
        docker rm -f campus_postgres campus_redis campus_nlp campus_backend campus_frontend campus_telegram_bot 2>/dev/null || true
        
        echo "🚀 Starting all services together..."
        $COMPOSE -f "$COMPOSE_FILE" up -d
        
        echo "⏳ Services starting up..."
        sleep 15
        
        echo "⏳ Waiting for AI engine to be ready..."
        
        # Wait for AI engine to be healthy with better checking
        for i in {1..30}; do
            if docker ps | grep -q "campus_nlp.*healthy"; then
                echo -e "${GREEN}✅ AI Engine is healthy!${NC}"
                break
            elif [ $i -eq 30 ]; then
                echo -e "${YELLOW}⚠️ AI Engine taking longer than expected (but may still work)${NC}"
            else
                echo -n "."
                sleep 2
            fi
        done
        
        # Test if AI is actually responding
        echo ""
        echo "🧪 Testing AI functionality..."
        if curl -s http://localhost:8001/docs | grep -q "swagger"; then
            echo -e "${GREEN}✅ AI API is responding!${NC}"
        else
            echo -e "${YELLOW}⚠️ AI API not ready yet (may need more time)${NC}"
        fi
        
        echo -e "${GREEN}✅ System startup completed!${NC}"
        echo ""
        echo "🌐 Access Points:"
        echo "• 🎓 Student Chat Interface: http://localhost:3008 (Main)"
        echo "• 🧠 AI API Documentation: http://localhost:8001/docs"
        echo "• 🔧 Backend API: http://localhost:3007/health"
        echo "• 🐘 Database: PostgreSQL on localhost:5433"
        echo "• 🔴 Cache: Redis on localhost:6380"
        echo ""
        echo "🧪 Quick Test Commands:"
        echo "• Test Hindi: ./run-campus-ai.sh test"
        echo "• Manual Test: curl -X POST http://localhost:8001/chat -H 'Content-Type: application/json' -d '{\"message\": \"मेरी फीस की जानकारी दें\", \"session_id\": \"test\"}'"
        echo ""
        echo "🤖 Optional Setup:"
        echo "• Setup Telegram Bot: ./setup-telegram.sh"
        echo "• Setup Real-time Features: ./setup-realtime.sh"
        echo ""
        echo -e "${GREEN}🎉 Your multilingual AI is ready to serve 2+ billion speakers!${NC}"
        ;;
        
    "stop")
        echo "⏹️ Stopping all services..."
        $COMPOSE -f "$COMPOSE_FILE" down
        echo -e "${GREEN}✅ All services stopped!${NC}"
        ;;
        
    "restart")
        echo "🔄 Restarting all services..."
        $0 stop
        sleep 3
        $0 start
        ;;
        
    "status")
        echo "📊 System Status:"
        echo "================"
        
        if docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q campus; then
            docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep campus
            echo ""
            
            # Check service accessibility
            echo "🌐 Service Health Check:"
            echo "========================"
            
            # Frontend check
            if curl -s -m 5 http://localhost:3008 >/dev/null 2>&1; then
                echo "✅ Frontend (3008): Accessible"
            else
                echo "❌ Frontend (3008): Not accessible"
            fi
            
            # Backend check  
            if curl -s -m 5 http://localhost:3007/health >/dev/null 2>&1; then
                echo "✅ Backend API (3007): Healthy"
            else
                echo "❌ Backend API (3007): Not responding"
            fi
            
            # AI API check
            if curl -s -m 5 http://localhost:8001/docs >/dev/null 2>&1; then
                echo "✅ AI API (8001): Responding"
            else
                echo "❌ AI API (8001): Not responding"
            fi
            
        else
            echo "No campus services running"
            echo ""
            echo "💡 Start services with: ./run-campus-ai.sh start"
        fi
        ;;
        
    "test")
        echo "🧪 Testing multilingual AI..."
        curl -s -X POST http://localhost:8001/chat \
            -H "Content-Type: application/json" \
            -d '{"message": "मेरी फीस की जानकारी दें", "session_id": "test"}' | \
            python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Language: {d.get(\"language\")}, Intent: {d.get(\"intent\")}')" 2>/dev/null || echo "Service not ready"
        ;;
        
    "logs")
        $COMPOSE -f "$COMPOSE_FILE" logs --tail=20
        ;;
        
    "telegram")
        ./setup-telegram.sh
        ;;
        
    *)
        echo "Usage: $0 {start|stop|restart|status|test|logs|telegram}"
        echo ""
        echo "Commands:"
        echo "  start    - Start all services"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services" 
        echo "  status   - Show running containers"
        echo "  test     - Test multilingual AI"
        echo "  logs     - Show system logs"
        echo "  telegram - Setup Telegram bot"
        echo ""
        echo "🌍 Supported Languages:"
        echo "Hindi, Bengali, Tamil, Telugu, Gujarati, Kannada, Malayalam, Punjabi, Urdu, Nepali, English"
        echo ""
        echo "💰 Cost: 100% FREE - Zero operational expenses"
        ;;
esac
