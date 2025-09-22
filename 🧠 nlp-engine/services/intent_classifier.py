"""
Intent Classification Service
Handles intent recognition using multilingual BERT models and rule-based patterns
"""

import asyncio
import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch
except ImportError:
    AutoTokenizer = None
    AutoModelForSequenceClassification = None
    pipeline = None
    torch = None

from utils.logger import setup_logger

logger = setup_logger(__name__)

class IntentClassifier:
    """
    Multilingual intent classification service for campus assistant
    
    Supported intents:
    - fee_inquiry: Fee-related questions
    - scholarship_info: Scholarship and financial aid
    - timetable_query: Schedule and timing information  
    - academic_policy: Rules and regulations
    - facility_info: Campus facilities and services
    - admission_help: Admission and registration
    - general_info: General institutional information
    - greeting: Greetings and pleasantries
    - complaint: Complaints and issues
    - unknown: Unrecognized intents
    """
    
    def __init__(self):
        self.available_intents = [
            "fee_inquiry",
            "scholarship_info", 
            "timetable_query",
            "academic_policy",
            "facility_info",
            "admission_help",
            "general_info",
            "greeting",
            "complaint",
            "unknown"
        ]
        
        # Intent patterns for different languages
        self.intent_patterns = {
            "fee_inquiry": {
                "en": [
                    r'\b(fee|fees|payment|tuition|cost|charge|bill|due|deadline|installment)\b',
                    r'\b(pay|paying|paid|money|amount|rupees|rs\.?)\b',
                    r'\b(semester|annual|monthly|late|fine|penalty)\b'
                ],
                "hi": [
                    r'\b(फीस|शुल्क|भुगतान|पैसा|रुपया|किस्त|जमा)\b',
                    r'\b(देना|भरना|जमा करना|अंतिम तारीख|समय सीमा)\b',
                    r'\b(सेमेस्टर|वार्षिक|मासिक|विलंब|जुर्माना)\b'
                ],
                "bn": [
                    r'\b(ফি|ফিস|পেমেন্ট|টাকা|পয়সা|কিস্তি|জমা)\b',
                    r'\b(দেওয়া|ভরা|জমা দেওয়া|শেষ তারিখ|সময়সীমা)\b',
                    r'\b(সেমিস্টার|বার্ষিক|মাসিক|বিলম্ব|জরিমানা)\b'
                ],
                "ta": [
                    r'\b(கட்டணம்|பணம்|ரூபாய்|தவணை|செலுத்த)\b',
                    r'\b(கொடுக்க|செலுத்த|கடைசி தேதி|காலக்கெடு)\b',
                    r'\b(செமஸ்டர்|வருடாந்திர|மாதாந்திர|தாமதம்|அபராதம்)\b'
                ],
                "mr": [
                    r'\b(फी|शुल्क|पेमेंट|पैसा|रुपया|हप्ता|जमा)\b',
                    r'\b(देणे|भरणे|जमा करणे|शेवटची तारीख|मुदत)\b',
                    r'\b(सेमेस्टर|वार्षिक|मासिक|उशीर|दंड)\b'
                ]
            },
            
            "scholarship_info": {
                "en": [
                    r'\b(scholarship|financial aid|grant|stipend|bursary|fellowship)\b',
                    r'\b(merit|need|sports|minority|sc|st|obc)\b',
                    r'\b(eligibility|criteria|apply|application|form)\b'
                ],
                "hi": [
                    r'\b(छात्रवृत्ति|वित्तीय सहायता|अनुदान|स्टाइपेंड)\b',
                    r'\b(मेधा|आवश्यकता|खेल|अल्पसंख्यक|एससी|एसटी|ओबीसी)\b',
                    r'\b(पात्रता|मानदंड|आवेदन|फॉर्म|अप्लाई)\b'
                ],
                "bn": [
                    r'\b(বৃত্তি|আর্থিক সাহায্য|অনুদান|স্টাইপেন্ড)\b',
                    r'\b(মেধা|প্রয়োজন|খেলা|সংখ্যালঘু|এসসি|এসটি|ওবিসি)\b',
                    r'\b(যোগ্যতা|মানদণ্ড|আবেদন|ফর্ম|আবেদন করা)\b'
                ],
                "ta": [
                    r'\b(உதவித்தொகை|நிதி உதவி|மானியம்|உதவித்தொகை)\b',
                    r'\b(தகுதி|தேவை|விளையாட்டு|சிறுபான்மை|எஸ்சி|எஸ்டி|ஓபிசி)\b',
                    r'\b(தகுதி|அளவுகோல்|விண்ணப்பம்|படிவம்|விண்ணப்பிக்க)\b'
                ],
                "mr": [
                    r'\b(शिष्यवृत्ती|आर्थिक मदत|अनुदान|स्टायपेंड)\b',
                    r'\b(गुणवत्ता|गरज|खेळ|अल्पसंख्याक|एससी|एसटी|ओबीसी)\b',
                    r'\b(पात्रता|निकष|अर्ज|फॉर्म|अर्ज करणे)\b'
                ]
            },
            
            "timetable_query": {
                "en": [
                    r'\b(timetable|schedule|class|lecture|exam|test|timing)\b',
                    r'\b(when|time|date|day|today|tomorrow|week)\b',
                    r'\b(subject|course|semester|year|period)\b'
                ],
                "hi": [
                    r'\b(समय सारणी|कक्षा|व्याख्यान|परीक्षा|टेस्ट|समय)\b',
                    r'\b(कब|समय|तारीख|दिन|आज|कल|सप्ताह)\b',
                    r'\b(विषय|कोर्स|सेमेस्टर|साल|पीरियड)\b'
                ],
                "bn": [
                    r'\b(সময়সূচী|ক্লাস|লেকচার|পরীক্ষা|টেস্ট|সময়)\b',
                    r'\b(কখন|সময়|তারিখ|দিন|আজ|কাল|সপ্তাহ)\b',
                    r'\b(বিষয়|কোর্স|সেমিস্টার|বছর|পিরিয়ড)\b'
                ],
                "ta": [
                    r'\b(நேர அட்டவணை|வகுப்பு|விரிவுரை|தேர்வு|டெஸ்ட்|நேரம்)\b',
                    r'\b(எப்போது|நேரம்|தேதி|நாள்|இன்று|நாளை|வாரம்)\b',
                    r'\b(பாடம்|கோர்ஸ்|செமஸ்டர்|வருடம்|பீரியட்)\b'
                ],
                "mr": [
                    r'\b(वेळापत्रक|वर्ग|व्याख्यान|परीक्षा|चाचणी|वेळ)\b',
                    r'\b(केव्हा|वेळ|तारीख|दिवस|आज|उद्या|आठवडा)\b',
                    r'\b(विषय|कोर्स|सेमेस्टर|वर्ष|पीरियड)\b'
                ]
            },
            
            "greeting": {
                "en": [
                    r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
                    r'\b(how are you|what\'s up|greetings|welcome)\b',
                    r'\b(thank you|thanks|bye|goodbye|see you)\b'
                ],
                "hi": [
                    r'\b(नमस्ते|हैलो|हाय|सुप्रभात|शुभ दोपहर|शुभ संध्या)\b',
                    r'\b(कैसे हैं|क्या हाल|धन्यवाद|शुक्रिया)\b',
                    r'\b(अलविदा|बाय|मिलते हैं|जय हिंद)\b'
                ],
                "bn": [
                    r'\b(নমস্কার|হ্যালো|হাই|সুপ্রভাত|শুভ দুপুর|শুভ সন্ধ্যা)\b',
                    r'\b(কেমন আছেন|কী খবর|ধন্যবাদ|শুকরিয়া)\b',
                    r'\b(বিদায়|বাই|দেখা হবে|জয় বাংলা)\b'
                ],
                "ta": [
                    r'\b(வணக்கம்|ஹலோ|ஹாய்|காலை வணக்கம்|மதிய வணক்கம்|மாலை வணக்கம்)\b',
                    r'\b(எப்படி இருக்கீங்க|என்ன விசேஷம்|நன்றி|தங்க்ஸ்)\b',
                    r'\b(போய் வருகிறேன்|பை|பார்க்கலாம்|வணக்கம்)\b'
                ],
                "mr": [
                    r'\b(नमस्कार|हॅलो|हाय|सुप्रभात|शुभ दुपार|शुभ संध्या)\b',
                    r'\b(कसे आहात|काय चालू आहे|धन्यवाद|शुक्रिया)\b',
                    r'\b(निरोप|बाय|भेटू|जय महाराष्ट्र)\b'
                ]
            }
        }
        
        # Confidence thresholds for different methods
        self.confidence_thresholds = {
            "transformer": 0.7,
            "pattern": 0.6,
            "keyword": 0.5,
            "fallback": 0.3
        }
        
        self.tokenizer = None
        self.model = None
        self.classifier_pipeline = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the intent classification models"""
        try:
            logger.info("Initializing Intent Classifier...")
            
            # Try to load multilingual BERT model
            if AutoTokenizer and AutoModelForSequenceClassification and torch:
                try:
                    model_name = "microsoft/DialoGPT-medium"  # Fallback model
                    # In production, use a fine-tuned multilingual model
                    # model_name = "bert-base-multilingual-cased"
                    
                    logger.info(f"Loading transformer model: {model_name}")
                    # For now, we'll use rule-based classification
                    # self.tokenizer = AutoTokenizer.from_pretrained(model_name)
                    # self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
                    
                except Exception as e:
                    logger.warning(f"Failed to load transformer model: {e}")
            
            self.is_initialized = True
            logger.info(f"Intent Classifier initialized. Available intents: {self.available_intents}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Intent Classifier: {e}")
            raise
    
    async def classify_intent(self, text: str, language: str = "en") -> Dict[str, Any]:
        """
        Classify intent of input text
        
        Args:
            text: Input text to classify
            language: Language of the text
            
        Returns:
            Dict containing intent, confidence, and extracted entities
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not text or not text.strip():
            return {
                "intent": "unknown",
                "confidence": 0.0,
                "entities": {},
                "method": "empty_input"
            }
        
        text = text.strip().lower()
        
        # Method 1: Pattern-based classification (most reliable for rule-based intents)
        pattern_result = self._classify_by_patterns(text, language)
        if pattern_result["confidence"] >= self.confidence_thresholds["pattern"]:
            return pattern_result
        
        # Method 2: Keyword-based classification
        keyword_result = self._classify_by_keywords(text, language)
        if keyword_result["confidence"] >= self.confidence_thresholds["keyword"]:
            return keyword_result
        
        # Method 3: Transformer-based classification (if available)
        if self.classifier_pipeline:
            transformer_result = await self._classify_with_transformer(text)
            if transformer_result["confidence"] >= self.confidence_thresholds["transformer"]:
                return transformer_result
        
        # Method 4: Fallback classification
        fallback_result = self._fallback_classification(text, language)
        
        # Return the best result
        best_result = max(
            [pattern_result, keyword_result, fallback_result],
            key=lambda x: x["confidence"]
        )
        
        return best_result
    
    def _classify_by_patterns(self, text: str, language: str) -> Dict[str, Any]:
        """Classify intent using regex patterns"""
        intent_scores = {}
        
        for intent, lang_patterns in self.intent_patterns.items():
            patterns = lang_patterns.get(language, lang_patterns.get("en", []))
            score = 0
            
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches
            
            if score > 0:
                intent_scores[intent] = score
        
        if not intent_scores:
            return {"intent": "unknown", "confidence": 0.0, "entities": {}, "method": "patterns"}
        
        # Find best intent
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        total_score = sum(intent_scores.values())
        confidence = best_intent[1] / total_score if total_score > 0 else 0.0
        
        # Extract entities based on intent
        entities = self._extract_entities(text, best_intent[0], language)
        
        return {
            "intent": best_intent[0],
            "confidence": min(confidence, 1.0),
            "entities": entities,
            "method": "patterns"
        }
    
    def _classify_by_keywords(self, text: str, language: str) -> Dict[str, Any]:
        """Classify intent using keyword matching"""
        # Define keywords for each intent
        intent_keywords = {
            "fee_inquiry": ["fee", "payment", "cost", "money", "rupees", "deadline", "due"],
            "scholarship_info": ["scholarship", "financial", "aid", "grant", "merit", "eligibility"],
            "timetable_query": ["timetable", "schedule", "class", "exam", "time", "when"],
            "academic_policy": ["rule", "regulation", "policy", "guideline", "procedure"],
            "facility_info": ["library", "hostel", "canteen", "lab", "facility", "campus"],
            "admission_help": ["admission", "registration", "enrollment", "apply", "form"],
            "general_info": ["contact", "address", "phone", "email", "information", "about"],
            "greeting": ["hello", "hi", "thanks", "thank", "bye", "goodbye"],
            "complaint": ["problem", "issue", "complaint", "wrong", "error", "help"]
        }
        
        intent_scores = {}
        words = text.split()
        
        for intent, keywords in intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            
            if score > 0:
                intent_scores[intent] = score / len(keywords)  # Normalize by keyword count
        
        if not intent_scores:
            return {"intent": "unknown", "confidence": 0.0, "entities": {}, "method": "keywords"}
        
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        return {
            "intent": best_intent[0],
            "confidence": min(best_intent[1], 1.0),
            "entities": {},
            "method": "keywords"
        }
    
    async def _classify_with_transformer(self, text: str) -> Dict[str, Any]:
        """Classify intent using transformer model"""
        try:
            if not self.classifier_pipeline:
                return {"intent": "unknown", "confidence": 0.0, "entities": {}, "method": "transformer"}
            
            # Use the pipeline to classify
            result = self.classifier_pipeline(text)
            
            # Map result to our intents
            predicted_label = result[0]["label"]
            confidence = result[0]["score"]
            
            # Map transformer labels to our intent system
            intent_mapping = {
                # Add mappings based on your trained model
                "LABEL_0": "general_info",
                "LABEL_1": "fee_inquiry",
                # ... add more mappings
            }
            
            mapped_intent = intent_mapping.get(predicted_label, "unknown")
            
            return {
                "intent": mapped_intent,
                "confidence": confidence,
                "entities": {},
                "method": "transformer"
            }
            
        except Exception as e:
            logger.warning(f"Transformer classification failed: {e}")
            return {"intent": "unknown", "confidence": 0.0, "entities": {}, "method": "transformer"}
    
    def _fallback_classification(self, text: str, language: str) -> Dict[str, Any]:
        """Fallback classification using simple heuristics"""
        # Check for question words
        question_words = {
            "en": ["what", "when", "where", "how", "why", "which", "who"],
            "hi": ["क्या", "कब", "कहाँ", "कैसे", "क्यों", "कौन", "किस"],
            "bn": ["কি", "কখন", "কোথায়", "কীভাবে", "কেন", "কোন", "কে"],
            "ta": ["என்ன", "எப்போது", "எங்கே", "எப்படி", "ஏன்", "எந்த", "யார்"],
            "mr": ["काय", "केव्हा", "कुठे", "कसे", "का", "कोण", "कोणत्या"]
        }
        
        words = question_words.get(language, question_words["en"])
        
        for word in words:
            if word in text:
                return {
                    "intent": "general_info",
                    "confidence": 0.4,
                    "entities": {},
                    "method": "fallback"
                }
        
        # Check for greetings
        if any(greeting in text for greeting in ["hello", "hi", "hey", "namaste", "namaskar"]):
            return {
                "intent": "greeting",
                "confidence": 0.5,
                "entities": {},
                "method": "fallback"
            }
        
        return {
            "intent": "unknown",
            "confidence": 0.2,
            "entities": {},
            "method": "fallback"
        }
    
    def _extract_entities(self, text: str, intent: str, language: str) -> Dict[str, Any]:
        """Extract entities based on intent and language"""
        entities = {}
        
        if intent == "fee_inquiry":
            # Extract fee-related entities
            amount_pattern = r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:rupees?|rs\.?|₹)?'
            amounts = re.findall(amount_pattern, text, re.IGNORECASE)
            if amounts:
                entities["amounts"] = amounts
            
            # Extract semester/year information
            semester_pattern = r'(semester|sem|year)\s*(\d+)'
            semesters = re.findall(semester_pattern, text, re.IGNORECASE)
            if semesters:
                entities["semesters"] = semesters
        
        elif intent == "timetable_query":
            # Extract date/time entities
            date_patterns = [
                r'(today|tomorrow|yesterday)',
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
            ]
            
            for pattern in date_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    entities.setdefault("dates", []).extend(matches)
            
            # Extract subject names (basic pattern)
            subject_pattern = r'\b([A-Z]{2,4}\d{3,4})\b'  # Course codes like CS101
            subjects = re.findall(subject_pattern, text)
            if subjects:
                entities["subjects"] = subjects
        
        elif intent == "scholarship_info":
            # Extract scholarship types
            scholarship_types = ["merit", "need", "sports", "minority", "sc", "st", "obc"]
            found_types = [t for t in scholarship_types if t in text.lower()]
            if found_types:
                entities["scholarship_types"] = found_types
        
        return entities
    
    def get_intent_description(self, intent: str, language: str = "en") -> str:
        """Get human-readable description of intent"""
        descriptions = {
            "en": {
                "fee_inquiry": "Questions about fees, payments, and financial matters",
                "scholarship_info": "Information about scholarships and financial aid",
                "timetable_query": "Questions about schedules, timetables, and timing",
                "academic_policy": "Questions about rules, regulations, and policies",
                "facility_info": "Information about campus facilities and services",
                "admission_help": "Help with admission and registration processes",
                "general_info": "General information about the institution",
                "greeting": "Greetings and pleasantries",
                "complaint": "Complaints and issues that need attention",
                "unknown": "Intent could not be determined"
            },
            "hi": {
                "fee_inquiry": "फीस, भुगतान और वित्तीय मामलों के बारे में प्रश्न",
                "scholarship_info": "छात्रवृत्ति और वित्तीय सहायता की जानकारी",
                "timetable_query": "समय सारणी और समय के बारे में प्रश्न",
                "academic_policy": "नियम, विनियम और नीतियों के बारे में प्रश्न",
                "facility_info": "परिसर की सुविधाओं और सेवाओं की जानकारी",
                "admission_help": "प्रवेश और पंजीकरण प्रक्रिया में सहायता",
                "general_info": "संस्थान के बारे में सामान्य जानकारी",
                "greeting": "अभिवादन और शिष्टाचार",
                "complaint": "शिकायतें और समस्याएं जिन पर ध्यान देने की आवश्यकता है",
                "unknown": "इरादा निर्धारित नहीं किया जा सका"
            }
        }
        
        return descriptions.get(language, descriptions["en"]).get(intent, "Unknown intent")
    
    async def batch_classify(self, texts: List[str], language: str = "en") -> List[Dict[str, Any]]:
        """Classify multiple texts"""
        results = []
        for text in texts:
            result = await self.classify_intent(text, language)
            results.append(result)
        return results
