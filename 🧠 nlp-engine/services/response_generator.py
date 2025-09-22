"""
Response Generation Service
Generates contextual responses based on intent, language, and conversation history
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ResponseGenerator:
    """
    Generates multilingual responses for campus assistant
    """
    
    def __init__(self):
        self.response_templates = {
            "fee_inquiry": {
                "en": [
                    "Fee payment deadlines are: Semester 1 - July 31st, Semester 2 - December 31st. Late fees apply after these dates.",
                    "You can pay fees online through the student portal or at the accounts office. Payment methods include net banking, UPI, and demand draft.",
                    "For fee structure details, please check the official fee notification on our website or contact the accounts department."
                ],
                "hi": [
                    "फीस भुगतान की अंतिम तारीख: सेमेस्टर 1 - 31 जुलाई, सेमेस्टर 2 - 31 दिसंबर। इन तारीखों के बाद विलंब शुल्क लागू होता है।",
                    "आप छात्र पोर्टल के माध्यम से या खाता कार्यालय में फीस का भुगतान कर सकते हैं। भुगतान के तरीकों में नेट बैंकिंग, UPI और डिमांड ड्राफ्ट शामिल हैं।",
                    "फीस संरचना के विवरण के लिए, कृपया हमारी वेबसाइट पर आधिकारिक फीस अधिसूचना देखें या खाता विभाग से संपर्क करें।"
                ]
            },
            "scholarship_info": {
                "en": [
                    "Available scholarships: Merit-based (80%+ marks), Need-based (family income <2L), Sports excellence, and Minority scholarships. Apply through the student portal.",
                    "Scholarship applications are open from June 1st to July 15th each year. Required documents include mark sheets, income certificate, and caste certificate (if applicable).",
                    "For scholarship eligibility and application process, visit the scholarship section on our website or contact the student welfare office."
                ],
                "hi": [
                    "उपलब्ध छात्रवृत्ति: मेधा आधारित (80%+ अंक), आवश्यकता आधारित (पारिवारिक आय <2L), खेल उत्कृष्टता, और अल्पसंख्यक छात्रवृत्ति। छात्र पोर्टल के माध्यम से आवेदन करें।",
                    "छात्रवृत्ति आवेदन हर साल 1 जून से 15 जुलाई तक खुले रहते हैं। आवश्यक दस्तावेजों में मार्क शीट, आय प्रमाण पत्र, और जाति प्रमाण पत्र (यदि लागू हो) शामिल हैं।",
                    "छात्रवृत्ति पात्रता और आवेदन प्रक्रिया के लिए, हमारी वेबसाइट पर छात्रवृत्ति अनुभाग देखें या छात्र कल्याण कार्यालय से संपर्क करें।"
                ]
            },
            "greeting": {
                "en": [
                    "Hello! I'm your campus assistant. How can I help you today?",
                    "Hi there! I'm here to help with your campus-related queries. What would you like to know?",
                    "Welcome! I can assist you with information about fees, scholarships, timetables, and more. How may I help?"
                ],
                "hi": [
                    "नमस्ते! मैं आपका कैंपस सहायक हूं। आज मैं आपकी कैसे मदद कर सकता हूं?",
                    "हैलो! मैं आपके कैंपस संबंधी प्रश्नों में मदद के लिए यहां हूं। आप क्या जानना चाहते हैं?",
                    "स्वागत है! मैं फीस, छात्रवृत्ति, समय सारणी और अन्य जानकारी में आपकी सहायता कर सकता हूं। मैं कैसे मदद कर सकता हूं?"
                ]
            },
            "unknown": {
                "en": [
                    "I'm not sure I understand your question. Could you please rephrase it or ask about fees, scholarships, timetables, or other campus services?",
                    "I didn't quite get that. I can help with information about academic matters, campus facilities, and administrative procedures. What would you like to know?",
                    "I'm here to help with campus-related queries. If you need assistance with something specific, please let me know and I'll do my best to help!"
                ],
                "hi": [
                    "मुझे यकीन नहीं है कि मैं आपका प्रश्न समझ पाया हूं। क्या आप इसे दोबारा कह सकते हैं या फीस, छात्रवृत्ति, समय सारणी, या अन्य कैंपस सेवाओं के बारे में पूछ सकते हैं?",
                    "मुझे वह समझ नहीं आया। मैं शैक्षणिक मामलों, कैंपस सुविधाओं और प्रशासनिक प्रक्रियाओं की जानकारी में मदद कर सकता हूं। आप क्या जानना चाहते हैं?",
                    "मैं कैंपस संबंधी प्रश्नों में मदद के लिए यहां हूं। यदि आपको किसी विशिष्ट चीज़ में सहायता चाहिए, तो कृपया मुझे बताएं और मैं मदद करने की पूरी कोशिश करूंगा!"
                ]
            }
        }
        
        self.escalation_triggers = [
            "complaint", "problem", "issue", "wrong", "error", "not working", "broken"
        ]
        
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize response generator"""
        try:
            logger.info("Initializing Response Generator...")
            self.is_initialized = True
            logger.info("Response Generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Response Generator: {e}")
            raise
    
    async def generate_response(
        self, 
        message: str, 
        intent: str, 
        language: str, 
        context: Dict[str, Any], 
        confidence: float
    ) -> Dict[str, Any]:
        """Generate response based on intent and context"""
        
        # Check if human escalation is needed
        escalate = self._should_escalate(message, intent, confidence, context)
        
        if escalate:
            response = self._get_escalation_response(language)
        else:
            response = self._get_intent_response(intent, language, context)
        
        return {
            "response": response,
            "escalate_to_human": escalate,
            "confidence": confidence
        }
    
    def _get_intent_response(self, intent: str, language: str, context: Dict[str, Any]) -> str:
        """Get response for specific intent"""
        templates = self.response_templates.get(intent, self.response_templates["unknown"])
        lang_templates = templates.get(language, templates.get("en", ["I can help you with campus queries."]))
        
        return random.choice(lang_templates)
    
    def _should_escalate(self, message: str, intent: str, confidence: float, context: Dict[str, Any]) -> bool:
        """Determine if query should be escalated to human"""
        # Low confidence threshold
        if confidence < 0.5:
            return True
        
        # Check for escalation trigger words
        message_lower = message.lower()
        if any(trigger in message_lower for trigger in self.escalation_triggers):
            return True
        
        # Check conversation context for repeated failures
        history = context.get("conversation_history", [])
        if len(history) > 3:
            recent_intents = [turn.get("intent") for turn in history[-3:]]
            if recent_intents.count("unknown") >= 2:
                return True
        
        return False
    
    def _get_escalation_response(self, language: str) -> str:
        """Get escalation response"""
        escalation_responses = {
            "en": "I'll connect you with a human staff member who can better assist you. Please wait a moment.",
            "hi": "मैं आपको एक मानव कर्मचारी से जोड़ूंगा जो आपकी बेहतर सहायता कर सकता है। कृपया एक क्षण प्रतीक्षा करें।"
        }
        
        return escalation_responses.get(language, escalation_responses["en"])
