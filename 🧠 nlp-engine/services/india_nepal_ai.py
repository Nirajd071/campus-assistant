"""
India & Nepal Multilingual AI Service
Free NLLB + Mistral pipeline for 15+ regional languages
"""

import os
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

logger = logging.getLogger(__name__)

class IndiaNepalAI:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # India & Nepal language codes for NLLB
        self.languages = {
            'en': 'eng_Latn', 'hi': 'hin_Deva', 'bn': 'ben_Beng', 
            'ta': 'tam_Taml', 'mr': 'mar_Deva', 'te': 'tel_Telu',
            'gu': 'guj_Gujr', 'kn': 'kan_Knda', 'ml': 'mal_Mlym',
            'pa': 'pan_Guru', 'ur': 'urd_Arab', 'ne': 'npi_Deva'
        }
        
        self.translation_model = None
        self.chat_pipeline = None
        asyncio.create_task(self._load_models())
    
    async def _load_models(self):
        """Load NLLB + lightweight reasoning model"""
        try:
            logger.info("🔄 Loading NLLB translation model...")
            # Load NLLB-200 distilled (600M - faster)
            model_name = "facebook/nllb-200-distilled-600M"
            self.translation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            logger.info("✅ NLLB model loaded successfully")
            
            # Load lightweight chat model
            logger.info("🔄 Loading chat model...")
            self.chat_pipeline = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                pad_token_id=50256
            )
            logger.info("✅ All models loaded successfully")
        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            logger.info("🔄 Running without NLLB models - using fallback responses")
    
    def detect_language(self, text: str) -> str:
        """Detect India/Nepal languages by script"""
        if any('\u0900' <= c <= '\u097F' for c in text):  # Devanagari
            if any(c in 'ऑॉळ' for c in text): return 'mr'  # Marathi
            if any(w in text for w in ['छ', 'भन्छ']): return 'ne'  # Nepali
            return 'hi'  # Hindi
        elif any('\u0980' <= c <= '\u09FF' for c in text): return 'bn'  # Bengali
        elif any('\u0B80' <= c <= '\u0BFF' for c in text): return 'ta'  # Tamil
        elif any('\u0C00' <= c <= '\u0C7F' for c in text): return 'te'  # Telugu
        elif any('\u0A80' <= c <= '\u0AFF' for c in text): return 'gu'  # Gujarati
        elif any('\u0C80' <= c <= '\u0CFF' for c in text): return 'kn'  # Kannada
        elif any('\u0D00' <= c <= '\u0D7F' for c in text): return 'ml'  # Malayalam
        elif any('\u0A00' <= c <= '\u0A7F' for c in text): return 'pa'  # Punjabi
        elif any('\u0600' <= c <= '\u06FF' for c in text): return 'ur'  # Urdu
        return 'en'  # Default English
    
    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> str:
        """Translate using NLLB"""
        if not self.translation_model or src_lang == tgt_lang:
            return text
        
        try:
            src_code = self.languages.get(src_lang, 'eng_Latn')
            tgt_code = self.languages.get(tgt_lang, 'eng_Latn')
            
            inputs = self.translation_tokenizer(text, return_tensors="pt", max_length=512, truncation=True)
            translated = self.translation_model.generate(
                **inputs,
                forced_bos_token_id=self.translation_tokenizer.convert_tokens_to_ids(tgt_code),
                max_length=512
            )
            return self.translation_tokenizer.decode(translated[0], skip_special_tokens=True)
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    async def translate_response(self, english_response: str, src_lang: str, target_lang: str) -> str:
        """Translate English response to target language using NLLB"""
        try:
            if target_lang == 'en':
                return english_response
            
            # Check if NLLB model is loaded
            if not self.translation_model:
                logger.warning("NLLB model not loaded, using fallback response")
                return self.get_fallback_response(target_lang)
            
            # Use NLLB to translate the response
            translated = await self.translate(english_response, src_lang, target_lang)
            logger.info(f"✅ NLLB translation: {src_lang} -> {target_lang}")
            return translated
            
        except Exception as e:
            logger.error(f"Response translation failed: {e}")
            # Fallback to high-quality responses for major languages
            return self.get_fallback_response(target_lang)
    
    def get_fallback_response(self, language: str) -> str:
        """Fallback responses in major Indian languages"""
        fallbacks = {
            'hi': "नमस्ते! मैं आपका कैंपस असिस्टेंट हूँ। मैं आपकी विश्वविद्यालय संबंधी सभी जानकारी में सहायता कर सकता हूँ। कृपया अपना प्रश्न पूछें।",
            'bn': "হ্যালো! আমি আপনার ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি আপনার বিশ্ববিদ্যালয় সম্পর্কিত সমস্ত তথ্যে সহায়তা করতে পারি। অনুগ্রহ করে আপনার প্রশ্ন জিজ্ঞাসা করুন।",
            'ta': "வணக்கம்! நான் உங்கள் கேம்பஸ் உதவியாளர். நான் உங்கள் பல்கலைக்கழகம் தொடர்பான அனைத்து தகவல்களிலும் உதவ முடியும். தயவுசெய்து உங்கள் கேள்வியைக் கேளுங்கள்।",
            'te': "నమస్కారం! నేను మీ క్యాంపస్ అసిస్టెంట్. నేను మీ విశ్వవిద్యాలయం సంబంధిత అన్ని సమాచారంలో సహాయం చేయగలను. దయచేసి మీ ప్రశ్న అడగండి।",
            'kn': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಕ್ಯಾಂಪಸ್ ಅಸಿಸ್ಟೆಂಟ್. ನಾನು ನಿಮ್ಮ ವಿಶ್ವವಿದ್ಯಾಲಯ ಸಂಬಂಧಿತ ಎಲ್ಲಾ ಮಾಹಿತಿಯಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು. ದಯವಿಟ್ಟು ನಿಮ್ಮ ಪ್ರಶ್ನೆ ಕೇಳಿ।",
            'ml': "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ കാമ്പസ് അസിസ്റ്റന്റ്. എനിക്ക് നിങ്ങളുടെ സർവകലാശാല സംബന്ധിച്ച എല്ലാ വിവരങ്ങളിലും സഹായിക്കാൻ കഴിയും. ദയവായി നിങ്ങളുടെ ചോദ്യം ചോദിക്കുക।",
            'mr': "नमस्कार! मी तुमचा कॅम्पस असिस्टंट आहे। मी तुमच्या विद्यापीठाशी संबंधित सर्व माहितीमध्ये मदत करू शकतो। कृपया तुमचा प्रश्न विचारा।",
            'gu': "નમસ્તે! હું તમારો કેમ્પસ આસિસ્ટન્ટ છું. હું તમારી યુનિવર્સિટી સંબંધિત તમામ માહિતીમાં મદદ કરી શકું છું. કૃપા કરીને તમારો પ્રશ્ન પૂછો।",
            'pa': "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਤੁਹਾਡਾ ਕੈਂਪਸ ਅਸਿਸਟੈਂਟ ਹਾਂ। ਮੈਂ ਤੁਹਾਡੀ ਯੂਨੀਵਰਸਿਟੀ ਨਾਲ ਸਬੰਧਤ ਸਾਰੀ ਜਾਣਕਾਰੀ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਸਵਾਲ ਪੁੱਛੋ।"
        }
        return fallbacks.get(language, "Hello! I'm your Campus Assistant. How can I help you today?")
    
    async def get_response(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Main multilingual pipeline"""
        try:
            # 1. Detect language
            detected_lang = self.detect_language(user_message)
            
            # 2. Translate to English if needed
            english_msg = user_message
            if detected_lang != 'en':
                english_msg = await self.translate(user_message, detected_lang, 'en')
            
            # 3. Generate response using chat model or template
            if self.chat_pipeline:
                campus_prompt = f"Student question: {english_msg}\nAs a helpful campus assistant, provide a clear and informative response about university services, fees, schedules, or general campus information:"
                try:
                    response = self.chat_pipeline(campus_prompt, max_new_tokens=200)
                    english_response = response[0]['generated_text'].replace(campus_prompt, "").strip()
                    if not english_response or len(english_response) < 10:
                        english_response = self.get_template_response(english_msg)
                except:
                    english_response = self.get_template_response(english_msg)
            else:
                english_response = self.get_template_response(english_msg)
            
            # 4. Translate back to user's language
            final_response = english_response
            if detected_lang != 'en':
                final_response = await self.translate(english_response, 'en', detected_lang)
            
            return {
                "response": final_response,
                "language": detected_lang,
                "english_version": english_msg if detected_lang != 'en' else None,
                "multilingual": True
            }
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {"response": "Technical error. Please try again.", "language": "en", "multilingual": False}
    
    def get_template_response(self, message: str) -> str:
        """Generate conversational, well-formatted response for common queries"""
        message_lower = message.lower()
        
        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "hey", "namaste"]):
            import random
            greetings = [
                "Hello! Welcome to our Campus Assistant. I'm delighted to help you with all your university-related questions.\n\nI can assist you with:\nFee information and payment guidance\nAcademic schedules and important dates\nLibrary services and resources\nAdmission procedures and requirements\nCampus facilities and general information\n\nPlease feel free to ask me anything. How may I assist you today?",
                "Hi there! I'm your Campus Assistant, here to help with any university-related queries.\n\nI can help you with:\nFee payments and deadlines\nClass schedules and exam dates\nLibrary hours and services\nAdmission information\nGeneral campus information\n\nWhat would you like to know about today?",
                "Namaste! I'm here to assist you with all your campus-related questions.\n\nI can provide information about:\nTuition fees and payment options\nAcademic calendars and schedules\nLibrary resources and services\nAdmission procedures\nCampus facilities\n\nHow can I help you today?"
            ]
            return random.choice(greetings)
        
        # Fee-related responses
        elif any(word in message_lower for word in ["fee", "payment", "cost", "tuition"]):
            return "I'd be happy to help you with fee information.\n\nFor the current academic year, here are the details:\n\nSemester Fee: ₹75,000\nPayment Due Date: July 31, 2024\nLate Fee: ₹5,000 (applicable after due date)\n\nConvenient Payment Options:\nOnline banking and UPI transfers\nCredit and Debit card payments\nBank transfer\nCash payment at the accounts office\n\nWould you like me to provide more details about any specific aspect of the fee structure or payment process?"
        
        # Schedule-related responses
        elif any(word in message_lower for word in ["schedule", "timetable", "class", "time"]):
            return "I can help you with academic schedule information.\n\n📚 **Current Semester**: Fall 2024\n📝 **Examination Period**: December 15-30, 2024\n🎉 **Winter Break**: Begins December 31, 2024\n\n**Additional Information:**\n• Regular classes are ongoing\n• Mid-term evaluations completed\n• Final exam schedule will be published soon\n\nWould you like information about specific class timings or any particular subject's schedule?"
        
        # Library-related responses
        elif any(word in message_lower for word in ["library", "book", "borrow"]):
            return "Here's comprehensive information about our library services:\n\n🕘 **Operating Hours**: 9:00 AM - 9:00 PM (Monday to Saturday)\n📍 **Location**: Central Library Building, Ground Floor\n📞 **Contact**: library@university.edu | Extension: 2345\n\n**Services Available:**\n• Book borrowing and returns\n• Digital resources and e-books\n• Study room reservations\n• Research assistance\n• Printing and scanning facilities\n\nIs there a specific book you're looking for, or do you need help with any particular library service?"
        
        # Admission-related responses
        elif any(word in message_lower for word in ["admission", "apply", "enrollment"]):
            return "I'm here to guide you through the admission process.\n\n📋 **Important Dates:**\n• Application Deadline: June 30, 2024\n• Entrance Examination: July 15, 2024\n• Results Announcement: August 1, 2024\n\n**Required Documents:**\n• Academic transcripts and certificates\n• Valid identity proof\n• Passport-size photographs\n• Application fee payment receipt\n\n**Application Process:**\n1. Online application submission\n2. Document verification\n3. Entrance exam (if applicable)\n4. Merit list publication\n\nWould you like detailed guidance on any specific step of the admission process?"
        
        # General helpful response
        else:
            return "Thank you for contacting our Campus Assistant! I'm here to provide you with comprehensive information about university services.\n\n**I can help you with:**\n• 💰 Fee payment information and deadlines\n• 📅 Academic calendars and exam schedules\n• 📚 Library services and study resources\n• 🎓 Admission procedures and requirements\n• 🏢 Campus facilities and contact information\n• 📞 Department contacts and office hours\n\nPlease let me know what specific information you're looking for, and I'll be happy to provide detailed assistance. What would you like to know about?"

# Supported languages info
SUPPORTED_LANGUAGES = {
    "Hindi": "हिंदी - 600M+ speakers",
    "Bengali": "বাংলা - 300M+ speakers", 
    "Tamil": "தமிழ் - 78M+ speakers",
    "Marathi": "मराठी - 83M+ speakers",
    "Telugu": "తెలుగు - 95M+ speakers",
    "Gujarati": "ગુજરાતી - 56M+ speakers",
    "Kannada": "ಕನ್ನಡ - 44M+ speakers",
    "Malayalam": "മലയാളം - 35M+ speakers",
    "Punjabi": "ਪੰਜਾਬੀ - 33M+ speakers",
    "Urdu": "اردو - 70M+ speakers",
    "Nepali": "नेपाली - 17M+ speakers",
    "English": "English - 1.5B+ speakers"
}
