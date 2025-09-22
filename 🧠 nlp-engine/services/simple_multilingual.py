"""
Simple Multilingual Service using LLM
"""

import os
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class SimpleMultilingualService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        if self.openai_api_key:
            self.client = OpenAI(
                base_url=self.openai_base_url,
                api_key=self.openai_api_key
            )
        else:
            self.client = None
    
    async def translate_response(self, text: str, target_language: str) -> str:
        """Translate campus assistant response using LLM"""
        if not self.client or target_language == 'en':
            return text
        
        try:
            languages = {
                'hi': 'Hindi (हिंदी)', 'bn': 'Bengali (বাংলা)', 'ta': 'Tamil (தமிழ்)', 
                'te': 'Telugu (తెలుగు)', 'kn': 'Kannada (ಕನ್ನಡ)', 'ml': 'Malayalam (മലയാളം)'
            }
            lang_name = languages.get(target_language, 'Hindi')
            
            system_prompt = f"""You are translating a university campus assistant's response to {lang_name}. 

CRITICAL: The user is NOT asking for translation help. They asked about university services and got a response in English. Now translate that response to {lang_name}.

RULES:
- Translate the ENTIRE response to {lang_name}
- Keep all numbers, dates, and specific information exactly the same
- Maintain the helpful, professional tone
- Keep the same structure and formatting
- Do NOT mention translation or ask for more text
- This is a direct translation of a campus assistant's answer"""
            
            import asyncio
            response = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Translate this campus assistant response to {lang_name}:\n\n{text}"}
                        ],
                        max_tokens=300,  # Reduced for faster response
                        temperature=0.3
                    )
                ),
                timeout=8.0  # 8 second timeout
            )
            
            translated = response.choices[0].message.content.strip()
            logger.info(f"✅ Translated response to {lang_name}: {translated[:50]}...")
            logger.info(f"Full translated response length: {len(translated)}")
            if not translated:
                logger.error("Translation returned empty string!")
                return self.get_fallback_response(target_language)
            return translated
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return self.get_fallback_response(target_language)
    
    def get_fallback_response(self, language: str) -> str:
        """Fallback responses"""
        fallbacks = {
            'hi': "नमस्ते! मैं KPRIET का कैंपस असिस्टेंट हूँ। मैं आपकी सहायता कर सकता हूँ।",
            'bn': "হ্যালো! আমি KPRIET এর ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি আপনাকে সাহায্য করতে পারি।",
            'ta': "வணக்கம்! நான் KPRIET இன் கேம்பஸ் உதவியாளர். நான் உங்களுக்கு உதவ முடியும்।"
        }
        return fallbacks.get(language, "Hello! I'm KPRIET Campus Assistant. How can I help you?")
