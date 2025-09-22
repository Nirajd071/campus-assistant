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
            # Load NLLB-200 distilled (600M - faster)
            model_name = "facebook/nllb-200-distilled-600M"
            self.translation_tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.translation_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            
            # Load lightweight chat model
            self.chat_pipeline = pipeline(
                "text-generation",
                model="microsoft/DialoGPT-small",
                pad_token_id=50256
            )
            logger.info("✅ Models loaded successfully")
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
    
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
    
    async def get_response(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Main multilingual pipeline"""
        try:
            # 1. Detect language
            detected_lang = self.detect_language(user_message)
            
            # 2. Translate to English if needed
            english_msg = user_message
            if detected_lang != 'en':
                english_msg = await self.translate(user_message, detected_lang, 'en')
            
            # 3. Generate response in English
            campus_prompt = f"University assistant helping with: {english_msg}\nResponse:"
            if self.chat_pipeline:
                response = self.chat_pipeline(campus_prompt, max_new_tokens=200)
                english_response = response[0]['generated_text'].replace(campus_prompt, "").strip()
            else:
                english_response = "I can help with campus information. Please try again."
            
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
