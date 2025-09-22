#!/bin/bash

# KPRIET Campus Assistant - Demo Startup Script
# Quick startup for submission demo

echo "🎓 KPRIET CAMPUS ASSISTANT - DEMO STARTUP"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Start all services
echo "🚀 Starting all services..."
docker-compose -f "./⚙️ Configuration Files/docker-compose.yml" up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🔍 Checking service health..."

# Check PostgreSQL
if docker exec campus_postgres pg_isready -U campus_user > /dev/null 2>&1; then
    echo "✅ PostgreSQL: Ready"
else
    echo "❌ PostgreSQL: Not ready"
fi

# Check Redis
if docker exec campus_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Ready"
else
    echo "❌ Redis: Not ready"
fi

# Check Backend API
if curl -s http://localhost:3007/health > /dev/null 2>&1; then
    echo "✅ Backend API: Ready"
else
    echo "❌ Backend API: Not ready"
fi

# Check NLP Engine
if curl -s http://localhost:8001/health > /dev/null 2>&1; then
    echo "✅ NLP Engine: Ready"
else
    echo "❌ NLP Engine: Not ready"
fi

# Check Frontend
if curl -s http://localhost:3008 > /dev/null 2>&1; then
    echo "✅ Frontend: Ready"
else
    echo "❌ Frontend: Not ready"
fi

echo ""
echo "🌐 DEMO ACCESS POINTS:"
echo "📱 Frontend Chat:     http://localhost:3008"
echo "🔧 Backend API:       http://localhost:3007"
echo "🧠 NLP Engine:        http://localhost:8001"
echo ""
echo "🧪 DEMO TESTING:"
echo "Run: python3 FINAL-DEMO-TEST.py"
echo ""
echo "📊 DEMO FEATURES:"
echo "✅ Multilingual support (English, Hindi, Bengali, Tamil)"
echo "✅ Real-time AI responses with NVIDIA integration"
echo "✅ University data integration"
echo "✅ Professional KPRIET branding"
echo "✅ Mobile-responsive design"
echo ""
echo "🎯 READY FOR SUBMISSION DEMO!"
