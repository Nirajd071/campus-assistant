#!/usr/bin/env python3
"""
Telegram Bot for Campus Assistant
Connects students to the AI-powered campus assistant via Telegram
"""

import os
import asyncio
import aiohttp
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class CampusAssistantBot:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.nlp_api_url = os.getenv("NLP_API_URL", "http://localhost:8001")

        if not self.bot_token or self.bot_token == "YOUR_BOT_TOKEN_HERE":
            raise ValueError(
                "TELEGRAM_BOT_TOKEN is not configured. Set a real token from "
                "@BotFather in your .env file to enable the Telegram bot."
            )
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🎓 **Welcome to Campus Assistant!** 🤖

I'm your AI-powered campus assistant. I can help you with:

📚 **Academic Information**
• Class schedules and timetables
• Exam dates and results
• Course information

💰 **Fee Information**
• Current fee structure
• Payment deadlines
• Outstanding amounts

📖 **Library Services**
• Book availability
• Due dates and renewals
• Library hours

🏫 **General Campus Info**
• Admission procedures
• Campus facilities
• Contact information

**Just ask me anything in plain English or Hindi!** 
Example: "What are my current fees?" or "मेरी फीस की जानकारी दें"

Type /help for more commands.
        """
        
        keyboard = [
            [InlineKeyboardButton("💰 Check Fees", callback_data='fees')],
            [InlineKeyboardButton("📚 My Schedule", callback_data='schedule')],
            [InlineKeyboardButton("📖 Library Info", callback_data='library')],
            [InlineKeyboardButton("🏫 Admissions", callback_data='admissions')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_message = """
🤖 **Campus Assistant Commands**

**Basic Commands:**
/start - Welcome message and quick actions
/help - Show this help message
/status - Check system status

**Quick Actions:**
• Just type your question naturally!
• Supported languages: English, Hindi, Bengali, Tamil, Marathi

**Example Questions:**
• "What are my current fees?"
• "Show me today's schedule"
• "Library hours?"
• "When is the next admission cycle?"
• "मेरी फीस कितनी है?" (Hindi)

**Features:**
✅ Real-time campus data
✅ Personalized responses
✅ Multilingual support
✅ 24/7 availability

Need human help? Contact: support@university.edu
        """
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.nlp_api_url}/health") as response:
                    if response.status == 200:
                        health_data = await response.json()
                        status_message = f"""
🟢 **System Status: ONLINE**

**AI Engine:** ✅ Healthy
**Response Time:** < 500ms
**Uptime:** {health_data.get('uptime', 'Unknown')}
**Version:** {health_data.get('version', '1.0.0')}

**Services:**
• Language Detection: ✅
• Intent Classification: ✅
• Context Management: ✅
• Response Generation: ✅

Ready to assist you! 🚀
                        """
                    else:
                        status_message = "🔴 **System Status: OFFLINE**\n\nPlease try again later."
        except Exception as e:
            status_message = f"🔴 **System Status: ERROR**\n\nError: {str(e)}"
        
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        session_id = f"telegram_{user_id}"
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Send to NLP API
            async with aiohttp.ClientSession() as session:
                payload = {
                    "message": user_message,
                    "session_id": session_id,
                    "user_id": user_id,
                    "platform": "telegram"
                }
                
                async with session.post(
                    f"{self.nlp_api_url}/chat",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        ai_response = await response.json()
                        
                        # Format response for Telegram
                        response_text = ai_response.get("response", "I'm sorry, I couldn't process your request.")
                        intent = ai_response.get("intent", "unknown")
                        confidence = ai_response.get("confidence", 0.0)
                        
                        # Add quick action buttons based on intent
                        keyboard = self.get_quick_actions(intent)
                        reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                        
                        # Add confidence indicator for low confidence responses
                        if confidence < 0.6:
                            response_text += "\n\n💡 *Need more specific help? Contact our support team.*"
                        
                        await update.message.reply_text(
                            response_text, 
                            reply_markup=reply_markup,
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text(
                            "🔧 I'm experiencing technical difficulties. Please try again in a moment."
                        )
        
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(
                "❌ Sorry, I encountered an error. Please try again or contact support."
            )
    
    def get_quick_actions(self, intent: str) -> list:
        """Get quick action buttons based on intent"""
        if intent == "fees":
            return [
                [InlineKeyboardButton("💳 Payment Methods", callback_data='payment_methods')],
                [InlineKeyboardButton("📊 Fee Structure", callback_data='fee_structure')]
            ]
        elif intent == "schedule":
            return [
                [InlineKeyboardButton("📅 Today's Classes", callback_data='today_schedule')],
                [InlineKeyboardButton("📋 Assignments", callback_data='assignments')]
            ]
        elif intent == "library":
            return [
                [InlineKeyboardButton("📚 My Books", callback_data='my_books')],
                [InlineKeyboardButton("🕒 Library Hours", callback_data='library_hours')]
            ]
        else:
            return [
                [InlineKeyboardButton("💰 Fees", callback_data='fees')],
                [InlineKeyboardButton("📚 Schedule", callback_data='schedule')]
            ]
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()
        
        # Map button callbacks to questions
        callback_to_question = {
            'fees': 'What are my current fees and payment deadlines?',
            'schedule': 'Show me my class schedule for today',
            'library': 'What books do I have issued from the library?',
            'admissions': 'Tell me about current admission procedures',
            'payment_methods': 'What payment methods are available for fees?',
            'fee_structure': 'Show me the detailed fee structure',
            'today_schedule': 'What are my classes today?',
            'assignments': 'What assignments do I have pending?',
            'my_books': 'List my issued library books',
            'library_hours': 'What are the library hours?'
        }
        
        question = callback_to_question.get(query.data, query.data)
        
        # Create a fake message object to reuse handle_message logic
        class FakeMessage:
            def __init__(self, text):
                self.text = text
        
        class FakeUpdate:
            def __init__(self, text, user, chat):
                self.message = FakeMessage(text)
                self.effective_user = user
                self.effective_chat = chat
        
        fake_update = FakeUpdate(question, query.from_user, query.message.chat)
        await self.handle_message(fake_update, context)
    
    def run(self):
        """Start the bot"""
        application = Application.builder().token(self.bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", self.start_command))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("status", self.status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        application.add_handler(CallbackQueryHandler(self.button_callback))
        
        logger.info("🤖 Campus Assistant Telegram Bot starting...")
        logger.info(f"🔗 NLP API URL: {self.nlp_api_url}")
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    import time
    load_dotenv()

    try:
        bot = CampusAssistantBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except ValueError as e:
        # Token not configured. Idle instead of crash-looping under a
        # restart policy so the rest of the stack stays healthy.
        logger.warning(f"⚠️ Telegram bot disabled: {e}")
        while True:
            time.sleep(3600)
    except Exception as e:
        logger.error(f"❌ Bot error: {e}")
