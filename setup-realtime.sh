#!/bin/bash

# 🚀 REAL-TIME CAMPUS AI SETUP SCRIPT

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 REAL-TIME CAMPUS AI SETUP${NC}"
echo "============================="
echo ""

# Function to prompt for university details
setup_university_integration() {
    echo -e "${YELLOW}📚 UNIVERSITY INTEGRATION SETUP${NC}"
    echo "=================================="
    echo ""
    
    echo "Please provide your university system details:"
    echo ""
    
    read -p "University ERP System URL: " erp_url
    read -p "ERP API Key: " erp_key
    read -p "Student Database URL: " student_db_url
    read -p "University SSO URL: " sso_url
    
    # Update .env file
    cat >> .env << EOF

# University Integration
UNIVERSITY_ERP_URL=$erp_url
ERP_API_KEY=$erp_key
STUDENT_DB_URL=$student_db_url
UNIVERSITY_SSO_URL=$sso_url

# Real-time Features
WEBSOCKET_PORT=3009
ENABLE_PUSH_NOTIFICATIONS=true
ENABLE_REAL_TIME_ANALYTICS=true
EOF
    
    echo -e "${GREEN}✅ University integration configured!${NC}"
}

# Function to set up WebSocket support
setup_websocket() {
    echo -e "${YELLOW}⚡ WEBSOCKET SETUP${NC}"
    echo "=================="
    echo ""
    
    # Install WebSocket dependencies
    cd "🔧 backend-api"
    npm install ws socket.io
    cd ..
    
    # Update docker-compose for WebSocket port
    if ! grep -q "3009:3009" "./⚙️ Configuration Files/docker-compose.yml"; then
        sed -i '/3007:3007/a\      - "3009:3009"' "./⚙️ Configuration Files/docker-compose.yml"
    fi
    
    echo -e "${GREEN}✅ WebSocket support added!${NC}"
}

# Function to set up production environment
setup_production() {
    echo -e "${YELLOW}🔒 PRODUCTION SETUP${NC}"
    echo "==================="
    echo ""
    
    read -p "Production domain (e.g., campus-ai.youruniversity.edu): " domain
    read -p "SSL certificate path: " ssl_cert
    read -p "SSL key path: " ssl_key
    
    # Create nginx configuration
    mkdir -p nginx
    cat > nginx/nginx.conf << EOF
server {
    listen 443 ssl http2;
    server_name $domain;
    
    ssl_certificate $ssl_cert;
    ssl_certificate_key $ssl_key;
    
    location / {
        proxy_pass http://frontend:3008;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /api/ {
        proxy_pass http://backend-api:3007;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
    
    location /ws/ {
        proxy_pass http://backend-api:3009;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF
    
    echo -e "${GREEN}✅ Production configuration created!${NC}"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${BLUE}🎯 REAL-TIME SETUP OPTIONS:${NC}"
    echo "============================"
    echo "1) 🎓 Set up University Integration"
    echo "2) ⚡ Enable WebSocket Real-time Chat"
    echo "3) 🔒 Configure Production Deployment"
    echo "4) 📊 Set up Analytics Dashboard"
    echo "5) 📱 Generate Mobile App Template"
    echo "6) 🔔 Configure Push Notifications"
    echo "7) 🧪 Test Real-time Features"
    echo "8) 📖 View Setup Documentation"
    echo "0) ❌ Exit"
    echo ""
    echo -n "Select option [0-8]: "
}

# Handle menu selection
handle_selection() {
    case $1 in
        1)
            setup_university_integration
            ;;
        2)
            setup_websocket
            ;;
        3)
            setup_production
            ;;
        4)
            echo -e "${YELLOW}📊 Analytics Dashboard Setup${NC}"
            echo "This will set up real-time analytics and monitoring."
            echo "Implementation details in REAL-TIME-SETUP.md"
            ;;
        5)
            echo -e "${YELLOW}📱 Mobile App Template${NC}"
            echo "Generating React Native template..."
            echo "Check REAL-TIME-SETUP.md for mobile integration guide"
            ;;
        6)
            echo -e "${YELLOW}🔔 Push Notifications Setup${NC}"
            echo "This will configure web push notifications for students."
            echo "Implementation guide in REAL-TIME-SETUP.md"
            ;;
        7)
            echo -e "${YELLOW}🧪 Testing Real-time Features${NC}"
            echo "Running real-time feature tests..."
            ./run-campus-ai.sh test
            ;;
        8)
            echo -e "${YELLOW}📖 Opening Documentation${NC}"
            if command -v code >/dev/null 2>&1; then
                code REAL-TIME-SETUP.md
            else
                cat REAL-TIME-SETUP.md
            fi
            ;;
        0)
            echo -e "${GREEN}Thank you for setting up Real-time Campus AI!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option. Please try again.${NC}"
            ;;
    esac
}

# Main execution
main() {
    while true; do
        show_menu
        read choice
        handle_selection $choice
        
        echo ""
        read -p "Press Enter to continue..."
    done
}

# Check if running with arguments
if [ $# -gt 0 ]; then
    case $1 in
        university)
            setup_university_integration
            ;;
        websocket)
            setup_websocket
            ;;
        production)
            setup_production
            ;;
        *)
            echo "Usage: $0 [university|websocket|production]"
            ;;
    esac
else
    main
fi
