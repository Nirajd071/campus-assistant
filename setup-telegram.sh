#!/bin/bash

# 🤖 TELEGRAM BOT SETUP SCRIPT

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🤖 TELEGRAM BOT SETUP${NC}"
echo "===================="
echo ""

echo -e "${YELLOW}📋 STEP 1: Create Telegram Bot${NC}"
echo "1. Open Telegram and search for @BotFather"
echo "2. Send: /newbot"
echo "3. Choose a name: Campus Assistant Bot"
echo "4. Choose a username: your_university_campus_bot"
echo "5. Copy the bot token"
echo ""

echo -n "Enter your bot token: "
read bot_token

if [ -z "$bot_token" ]; then
    echo "❌ No token provided. Exiting."
    exit 1
fi

echo ""
echo -e "${YELLOW}📝 STEP 2: Updating Configuration${NC}"

# Update .env file
sed -i "s/TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE/TELEGRAM_BOT_TOKEN=$bot_token/" .env

echo -e "${GREEN}✅ Configuration updated!${NC}"
echo ""

echo -e "${YELLOW}🚀 STEP 3: Restarting System${NC}"
./run-campus-ai.sh restart

echo ""
echo -e "${GREEN}🎉 TELEGRAM BOT SETUP COMPLETE!${NC}"
echo ""
echo "📱 Your bot is now ready! Students can:"
echo "• Search for your bot on Telegram"
echo "• Send messages in Hindi: मेरी फीस की जानकारी दें"
echo "• Send messages in Bengali: আমার ক্লাসের সময়সূচী কী?"
echo "• Get instant multilingual responses!"
echo ""
echo -e "${BLUE}🌍 Your multilingual AI now serves students on Telegram!${NC}"
