"""
Language Detection Service
Handles automatic detection of user input language using FastText and langdetect
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
import re
import os

try:
    import fasttext
except ImportError:
    fasttext = None

try:
    from langdetect import detect, detect_langs, LangDetectException
except ImportError:
    detect = None
    detect_langs = None
    LangDetectException = Exception

from utils.logger import setup_logger

logger = setup_logger(__name__)

class LanguageDetector:
    """
    Multilingual language detection service supporting:
    - English (en)
    - Hindi (hi) 
    - Bengali (bn)
    - Tamil (ta)
    - Marathi (mr)
    """
    
    def __init__(self):
        self.supported_languages = ["en", "hi", "bn", "ta", "mr"]
        self.language_names = {
            "en": "English",
            "hi": "Hindi",
            "bn": "Bengali", 
            "ta": "Tamil",
            "mr": "Marathi"
        }
        
        # Language-specific patterns for better detection
        self.language_patterns = {
            "hi": re.compile(r'[\u0900-\u097F]+'),  # Devanagari script
            "bn": re.compile(r'[\u0980-\u09FF]+'),  # Bengali script
            "ta": re.compile(r'[\u0B80-\u0BFF]+'),  # Tamil script
            "mr": re.compile(r'[\u0900-\u097F]+'),  # Devanagari script (same as Hindi)
        }
        
        # Common words for each language (for pattern matching)
        self.common_words = {
            "hi": ["क्या", "कैसे", "कब", "कहाँ", "क्यों", "है", "हैं", "का", "की", "के", "में", "से", "को", "पर"],
            "bn": ["কি", "কীভাবে", "কখন", "কোথায়", "কেন", "আছে", "আছেন", "এর", "এই", "সেই", "মধ্যে", "থেকে", "কে", "উপর"],
            "ta": ["என்ன", "எப்படி", "எப்போது", "எங்கே", "ஏன்", "இருக்கிறது", "இருக்கிறார்", "இன்", "இந்த", "அந்த", "இல்", "இருந்து", "க்கு", "மேல்"],
            "mr": ["काय", "कसे", "केव्हा", "कुठे", "का", "आहे", "आहेत", "चा", "ची", "चे", "मध्ये", "पासून", "ला", "वर"],
            "en": ["what", "how", "when", "where", "why", "is", "are", "the", "a", "an", "in", "on", "at", "to", "for"]
        }
        
        self.fasttext_model = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the language detection models"""
        try:
            logger.info("Initializing Language Detector...")
            
            # Try to load FastText model if available
            if fasttext:
                try:
                    # Download language identification model if not exists
                    model_path = "lid.176.bin"
                    if not os.path.exists(model_path):
                        logger.info("Downloading FastText language identification model...")
                        # In production, download from FastText official source
                        # For now, we'll use langdetect as primary
                        pass
                    else:
                        self.fasttext_model = fasttext.load_model(model_path)
                        logger.info("FastText model loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to load FastText model: {e}")
            
            self.is_initialized = True
            logger.info(f"Language Detector initialized. Supported languages: {self.supported_languages}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Language Detector: {e}")
            raise
    
    async def detect_language(self, text: str) -> Dict[str, any]:
        """
        Detect language of input text
        
        Args:
            text: Input text to detect language for
            
        Returns:
            Dict containing language code, confidence, and detection method
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not text or not text.strip():
            return {
                "language": "en",  # Default to English
                "confidence": 0.5,
                "method": "default"
            }
        
        text = text.strip()
        
        # Method 1: Script-based detection (most reliable for Indian languages)
        script_result = self._detect_by_script(text)
        if script_result["confidence"] > 0.8:
            return script_result
        
        # Method 2: Pattern matching with common words
        pattern_result = self._detect_by_patterns(text)
        if pattern_result["confidence"] > 0.7:
            return pattern_result
        
        # Method 3: Use langdetect library
        if detect and detect_langs:
            langdetect_result = await self._detect_with_langdetect(text)
            if langdetect_result["confidence"] > 0.6:
                return langdetect_result
        
        # Method 4: Use FastText if available
        if self.fasttext_model:
            fasttext_result = await self._detect_with_fasttext(text)
            if fasttext_result["confidence"] > 0.5:
                return fasttext_result
        
        # Fallback: Return the best result or default to English
        best_result = max(
            [script_result, pattern_result],
            key=lambda x: x["confidence"]
        )
        
        if best_result["confidence"] > 0.3:
            return best_result
        
        return {
            "language": "en",
            "confidence": 0.5,
            "method": "fallback"
        }
    
    def _detect_by_script(self, text: str) -> Dict[str, any]:
        """Detect language based on Unicode script ranges"""
        script_counts = {}
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                for lang, pattern in self.language_patterns.items():
                    if pattern.search(char):
                        script_counts[lang] = script_counts.get(lang, 0) + 1
        
        if total_chars == 0:
            return {"language": "en", "confidence": 0.0, "method": "script"}
        
        # Find dominant script
        if script_counts:
            dominant_lang = max(script_counts.items(), key=lambda x: x[1])
            confidence = dominant_lang[1] / total_chars
            
            # Special handling for Hindi vs Marathi (both use Devanagari)
            if dominant_lang[0] in ["hi", "mr"] and confidence > 0.5:
                # Use word patterns to distinguish
                word_result = self._detect_by_patterns(text)
                if word_result["language"] in ["hi", "mr"]:
                    return word_result
            
            return {
                "language": dominant_lang[0],
                "confidence": confidence,
                "method": "script"
            }
        
        return {"language": "en", "confidence": 0.0, "method": "script"}
    
    def _detect_by_patterns(self, text: str) -> Dict[str, any]:
        """Detect language based on common word patterns"""
        text_lower = text.lower()
        word_counts = {}
        
        for lang, words in self.common_words.items():
            count = 0
            for word in words:
                if lang == "en":
                    # For English, check word boundaries
                    count += len(re.findall(r'\b' + re.escape(word.lower()) + r'\b', text_lower))
                else:
                    # For Indian languages, simple substring matching
                    count += text.count(word)
            word_counts[lang] = count
        
        if not any(word_counts.values()):
            return {"language": "en", "confidence": 0.0, "method": "patterns"}
        
        # Find language with most matches
        dominant_lang = max(word_counts.items(), key=lambda x: x[1])
        total_matches = sum(word_counts.values())
        
        if total_matches > 0:
            confidence = dominant_lang[1] / total_matches
            return {
                "language": dominant_lang[0],
                "confidence": confidence,
                "method": "patterns"
            }
        
        return {"language": "en", "confidence": 0.0, "method": "patterns"}
    
    async def _detect_with_langdetect(self, text: str) -> Dict[str, any]:
        """Detect language using langdetect library"""
        try:
            # Get all possible languages with probabilities
            lang_probs = detect_langs(text)
            
            # Find the best supported language
            for lang_prob in lang_probs:
                lang_code = lang_prob.lang
                
                # Map some common language codes
                lang_mapping = {
                    "hi": "hi",
                    "bn": "bn", 
                    "ta": "ta",
                    "mr": "mr",
                    "en": "en"
                }
                
                mapped_lang = lang_mapping.get(lang_code)
                if mapped_lang and mapped_lang in self.supported_languages:
                    return {
                        "language": mapped_lang,
                        "confidence": lang_prob.prob,
                        "method": "langdetect"
                    }
            
            # If no supported language found, return English
            return {"language": "en", "confidence": 0.5, "method": "langdetect"}
            
        except (LangDetectException, Exception) as e:
            logger.warning(f"Langdetect failed: {e}")
            return {"language": "en", "confidence": 0.0, "method": "langdetect"}
    
    async def _detect_with_fasttext(self, text: str) -> Dict[str, any]:
        """Detect language using FastText model"""
        try:
            if not self.fasttext_model:
                return {"language": "en", "confidence": 0.0, "method": "fasttext"}
            
            # Predict language
            predictions = self.fasttext_model.predict(text.replace('\n', ' '), k=5)
            labels, scores = predictions
            
            # Find best supported language
            for label, score in zip(labels, scores):
                # FastText returns labels like '__label__en'
                lang_code = label.replace('__label__', '')
                
                if lang_code in self.supported_languages:
                    return {
                        "language": lang_code,
                        "confidence": float(score),
                        "method": "fasttext"
                    }
            
            return {"language": "en", "confidence": 0.5, "method": "fasttext"}
            
        except Exception as e:
            logger.warning(f"FastText detection failed: {e}")
            return {"language": "en", "confidence": 0.0, "method": "fasttext"}
    
    def get_language_name(self, lang_code: str) -> str:
        """Get human-readable language name"""
        return self.language_names.get(lang_code, lang_code)
    
    def is_supported_language(self, lang_code: str) -> bool:
        """Check if language is supported"""
        return lang_code in self.supported_languages
    
    async def detect_batch(self, texts: List[str]) -> List[Dict[str, any]]:
        """Detect languages for multiple texts"""
        results = []
        for text in texts:
            result = await self.detect_language(text)
            results.append(result)
        return results
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages with names"""
        return [
            {"code": code, "name": name}
            for code, name in self.language_names.items()
        ]
