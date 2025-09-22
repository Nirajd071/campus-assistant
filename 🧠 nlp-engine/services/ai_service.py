"""
Real-time AI Service with OpenAI/Gemini Integration
Fetches live data and generates intelligent responses
"""

import os
import json
import asyncio
import httpx
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from openai import OpenAI
import google.generativeai as genai
from .simple_multilingual import SimpleMultilingualService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check if Gemini is available
GEMINI_AVAILABLE = True
try:
    import google.generativeai as genai
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Gemini AI not available - install google-generativeai package")

class RealTimeAIService:
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.university_api_base = os.getenv("UNIVERSITY_API_BASE", "https://api.university.edu")
        self.university_api_key = os.getenv("UNIVERSITY_API_KEY")
        self.nllb_translator_url = os.getenv("NLLB_TRANSLATOR_URL", "http://nllb-translator:8002")
        self.use_openai = bool(self.openai_api_key)
        self.use_gemini = bool(self.gemini_api_key)
        
        # Initialize OpenAI client with NVIDIA API
        if self.use_openai:
            from openai import OpenAI
            self.openai_client = OpenAI(
                base_url=self.openai_base_url,
                api_key=self.openai_api_key
            )
            logger.info(f"✅ OpenAI client initialized with base URL: {self.openai_base_url}")
            logger.info(f"✅ Using model: {self.openai_model}")
            
        if self.use_gemini and GEMINI_AVAILABLE:
            genai.configure(api_key=self.gemini_api_key)
            
        # Initialize simple multilingual service
        self.multilingual_service = SimpleMultilingualService()
        self.supported_languages = ['en', 'hi', 'bn', 'ta', 'te', 'kn', 'ml', 'mr', 'gu', 'pa']
    
    async def get_multilingual_response(
        self, 
        user_message: str, 
        context: Dict[str, Any],
        student_id: Optional[str] = None,
        preferred_language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate multilingual response using NVIDIA AI with language preference
        """
        try:
            # Use preferred language from frontend or detect from message
            target_language = preferred_language or context.get('language', 'en')
            
            # Analyze intent first
            intent_analysis = await self.analyze_intent(user_message)
            
            # Fetch live data based on intent
            live_data = await self.fetch_live_data(intent_analysis, student_id)
            
            # Generate response directly in the user's selected language
            if target_language != 'en':
                # Generate response directly in the selected language using AI
                try:
                    response = await self.generate_multilingual_openai_response(
                        user_message, intent_analysis, live_data, context, target_language
                    )
                    if not response or response.strip() == "":
                        logger.warning(f"Empty AI response, using template for {target_language}")
                        response = self.get_multilingual_template_response(intent_analysis.get("intent", "general"), target_language, live_data)
                    logger.info(f"✅ Direct {target_language} response generated")
                except Exception as e:
                    logger.error(f"Direct {target_language} response failed: {e}")
                    # Fallback to templates
                    response = self.get_multilingual_template_response(intent_analysis.get("intent", "general"), target_language, live_data)
            else:
                # Generate English response
                response = await self.generate_openai_response(
                    user_message, intent_analysis, live_data, context
                )
            
            return {
                "response": response,
                "language": target_language,
                "english_translation": user_message if target_language != 'en' else None,
                "intent": intent_analysis.get("intent", "general"),
                "confidence": intent_analysis.get("confidence", 0.7),
                "data_sources": live_data.get("sources", []),
                "personalized": bool(student_id),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Multilingual AI error: {e}")
            # Fallback to regular AI response
            return await self.get_intelligent_response(user_message, context, student_id)
    
    async def enhance_with_live_data(self, response: str, live_data: Dict, language: str) -> str:
        """Enhance response with live university data in the detected language"""
        if not live_data.get("data"):
            return response
        
        # Add live data context in the appropriate language
        data_context = ""
        if language == 'hi':  # Hindi
            data_context = f"\n\nवर्तमान जानकारी: {json.dumps(live_data.get('data', {}), ensure_ascii=False)}"
        elif language == 'bn':  # Bengali
            data_context = f"\n\nবর্তমান তথ্য: {json.dumps(live_data.get('data', {}), ensure_ascii=False)}"
        elif language == 'ta':  # Tamil
            data_context = f"\n\nதற்போதைய தகவல்: {json.dumps(live_data.get('data', {}), ensure_ascii=False)}"
        elif language == 'ne':  # Nepali
            data_context = f"\n\nहालको जानकारी: {json.dumps(live_data.get('data', {}), ensure_ascii=False)}"
        else:  # English or others
            data_context = f"\n\nCurrent Information: {json.dumps(live_data.get('data', {}))}"
        
        return response + data_context
            
    async def get_intelligent_response(
        self, 
        user_message: str, 
        context: Dict[str, Any],
        student_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate intelligent response using AI + live data
        """
        try:
            # 1. Analyze user intent and extract entities
            intent_analysis = await self.analyze_intent(user_message)
            
            # 2. Fetch relevant live data based on intent
            live_data = await self.fetch_live_data(intent_analysis, student_id)
            
            # 3. Generate AI response with live data context
            ai_response = await self.generate_ai_response(
                user_message, intent_analysis, live_data, context
            )
            
            return {
                "response": ai_response,
                "intent": intent_analysis["intent"],
                "confidence": intent_analysis["confidence"],
                "data_sources": live_data.get("sources", []),
                "personalized": bool(student_id),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"AI Service error: {e}")
            return await self.fallback_response(user_message, context)
    
    async def analyze_intent(self, message: str) -> Dict[str, Any]:
        """
        Use AI to analyze user intent and extract entities
        """
        system_prompt = """
        You are an intelligent intent analyzer for a university chatbot.
        Analyze the user message and return JSON with:
        - intent: main category (fees, admissions, schedules, grades, etc.)
        - entities: extracted information (dates, amounts, course names, etc.)
        - confidence: 0.0-1.0 confidence score
        - data_needed: what live data should be fetched
        """
        
        if self.use_openai:
            try:
                completion = self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.3,
                    max_tokens=500
                )
                
                result = json.loads(completion.choices[0].message.content)
                return result
                
            except Exception as e:
                logger.error(f"NVIDIA OpenAI intent analysis failed: {e}")
        
        # Fallback to pattern-based analysis
        return await self.pattern_based_intent(message)
    
    async def fetch_live_data(self, intent_analysis: Dict, student_id: Optional[str]) -> Dict[str, Any]:
        """
        Fetch real-time data from university APIs
        """
        intent = intent_analysis.get("intent", "")
        data_needed = intent_analysis.get("data_needed", [])
        
        live_data = {"sources": [], "data": {}}
        
        # Use mock data for demo - university API integration would be added here
        # Fee Information
        if "fees" in intent or "payment" in intent:
            fee_data = self.get_default_fee_data()
            live_data["data"]["fees"] = fee_data
            live_data["sources"].append("Fee Management System")
        
        # Academic Schedule
        if "schedule" in intent or "timetable" in intent:
            schedule_data = self.get_default_schedule_data()
            live_data["data"]["schedule"] = schedule_data
            live_data["sources"].append("Academic Management System")
        
        # Admission Information
        if "admission" in intent or "enrollment" in intent:
            admission_data = self.get_default_admission_data()
            live_data["data"]["admission"] = admission_data
            live_data["sources"].append("Admission Portal")
        
        # Student Grades
        if "grade" in intent or "result" in intent and student_id:
            grade_data = {"current_gpa": 8.5, "semester": "Fall 2024", "status": "Good Standing"}
            live_data["data"]["grades"] = grade_data
            live_data["sources"].append("Student Information System")
        
        # Library Information
        if "library" in intent or "book" in intent:
            library_data = self.get_default_library_data()
            live_data["data"]["library"] = library_data
            live_data["sources"].append("Library Management System")
        
        # Student Information (if student_id provided)
        if student_id:
            student_info = {"name": "Demo Student", "id": student_id, "program": "Computer Science", "year": "3rd Year"}
            live_data["data"]["student_info"] = student_info
            live_data["sources"].append("Student Information System")
        
        return live_data
    
    async def fetch_fee_data(self, session: aiohttp.ClientSession, student_id: Optional[str]) -> Dict:
        """Fetch real-time fee information"""
        try:
            # Generic fee structure
            url = f"{self.university_api_base}/fees/current"
            async with session.get(url) as response:
                if response.status == 200:
                    fee_structure = await response.json()
                else:
                    fee_structure = self.get_default_fee_data()
            
            # Student-specific fees if ID provided
            if student_id:
                url = f"{self.university_api_base}/students/{student_id}/fees"
                async with session.get(url) as response:
                    if response.status == 200:
                        student_fees = await response.json()
                        fee_structure.update(student_fees)
            
            return fee_structure
            
        except Exception as e:
            logger.error(f"Fee data fetch failed: {e}")
            return self.get_default_fee_data()
    
    async def fetch_schedule_data(self, session: aiohttp.ClientSession, student_id: Optional[str]) -> Dict:
        """Fetch real-time schedule information"""
        try:
            if student_id:
                # Student-specific schedule
                url = f"{self.university_api_base}/students/{student_id}/schedule"
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            
            # General schedule
            url = f"{self.university_api_base}/schedule/current"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return self.get_default_schedule_data()
                    
        except Exception as e:
            logger.error(f"Schedule data fetch failed: {e}")
            return self.get_default_schedule_data()
    
    async def fetch_admission_data(self, session: aiohttp.ClientSession) -> Dict:
        """Fetch real-time admission information"""
        try:
            url = f"{self.university_api_base}/admissions/current"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return self.get_default_admission_data()
                    
        except Exception as e:
            logger.error(f"Admission data fetch failed: {e}")
            return self.get_default_admission_data()
    
    async def fetch_grade_data(self, session: aiohttp.ClientSession, student_id: str) -> Dict:
        """Fetch student grades"""
        try:
            url = f"{self.university_api_base}/students/{student_id}/grades"
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": "Grades not available"}
                    
        except Exception as e:
            logger.error(f"Grade data fetch failed: {e}")
            return {"error": "Unable to fetch grades"}
    
    async def fetch_library_data(self, session: aiohttp.ClientSession, student_id: Optional[str]) -> Dict:
        """Fetch library information"""
        try:
            # General library info
            url = f"{self.university_api_base}/library/info"
            async with session.get(url) as response:
                if response.status == 200:
                    library_info = await response.json()
                else:
                    library_info = self.get_default_library_data()
            
            # Student-specific library data
            if student_id:
                url = f"{self.university_api_base}/library/student/{student_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        student_library = await response.json()
                        library_info.update(student_library)
            
            return library_info
            
        except Exception as e:
            logger.error(f"Library data fetch failed: {e}")
            return self.get_default_library_data()
    
    async def generate_ai_response(
        self, 
        user_message: str, 
        intent_analysis: Dict, 
        live_data: Dict, 
        context: Dict
    ) -> str:
        """
        Generate intelligent response using AI with live data
        """
        if self.use_gemini and GEMINI_AVAILABLE:
            return await self.generate_gemini_response(user_message, intent_analysis, live_data, context)
        elif self.use_openai:
            return await self.generate_openai_response(user_message, intent_analysis, live_data, context)
        else:
            return await self.generate_template_response(intent_analysis, live_data)
    
    async def generate_gemini_response(self, user_message: str, intent_analysis: Dict, live_data: Dict, context: Dict) -> str:
        """Generate response using Google Gemini with live data"""
        try:
            prompt = f"""
            You are a helpful university assistant with access to real-time campus data.
            
            Student's question: {user_message}
            Intent: {intent_analysis.get('intent', 'general')}
            
            Available live data:
            {json.dumps(live_data.get('data', {}), indent=2)}
            
            Context: {json.dumps(context, indent=2)}
            
            Please provide a helpful, accurate response using the live data. Be conversational and personalized.
            If specific data is missing, acknowledge it and provide general guidance.
            Keep responses concise but informative.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.gemini_model.generate_content(prompt)
            )
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Gemini response generation failed: {e}")
            return await self.generate_template_response(intent_analysis, live_data)
    
    async def generate_openai_response(self, user_message: str, intent_analysis: Dict, live_data: Dict, context: Dict) -> str:
        """Generate response using NVIDIA OpenAI API with live data"""
        try:
            # Prepare university data context
            data_context = ""
            if live_data.get("data"):
                data_context = f"Available University Data: {json.dumps(live_data['data'], indent=2)}"
            
            prompt = f"""You are a professional university campus assistant helping students with their queries.

Student Query: {user_message}
Intent: {intent_analysis.get('intent', 'general')}
{data_context}

Instructions:
- Provide accurate, helpful information based on available data
- If specific data is not available, provide general guidance
- Be conversational, professional, and supportive
- Format responses clearly with proper line breaks
- Don't use markdown formatting (**, •) as this is for web display
- Each point should be on a separate line
- Ask follow-up questions to be more helpful

Respond naturally as a university assistant would."""

            # Add timeout for NVIDIA API call
            import asyncio
            completion = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {"role": "system", "content": "You are a helpful university campus assistant. Provide clear, well-formatted responses without markdown."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        top_p=1,
                        max_tokens=512,  # Reduced for faster response
                        stream=False
                    )
                ),
                timeout=10.0  # 10 second timeout
            )
            
            # Check for reasoning content (if available)
            reasoning = getattr(completion.choices[0].message, "reasoning_content", None)
            if reasoning:
                logger.info(f"AI Reasoning: {reasoning[:100]}...")
            
            response = completion.choices[0].message.content.strip()
            logger.info(f"✅ NVIDIA OpenAI response generated successfully")
            return response
            
        except Exception as e:
            logger.error(f"NVIDIA OpenAI response generation failed: {e}")
            return await self.generate_template_response(intent_analysis, live_data)
    
    async def pattern_based_intent(self, message: str) -> Dict[str, Any]:
        """Enhanced pattern-based intent analysis with conversational context"""
        message_lower = message.lower()
        
        # Greeting patterns (including Tamil வணக்கம்)
        if any(word in message_lower for word in ["hello", "hi", "hey", "namaste", "good morning", "good afternoon", "how are you", "வணக்கம்", "नमस्ते", "হ্যালো"]):
            return {"intent": "greeting", "confidence": 0.9, "data_needed": []}
        
        # Fee patterns (including Hindi/Bengali/Tamil words)
        elif any(word in message_lower for word in ["fee", "payment", "tuition", "cost", "money", "pay", "फीस", "पैसा", "টাকা", "ফি", "கட்டணம்", "பணம்"]):
            return {"intent": "fees", "confidence": 0.8, "data_needed": ["fees"]}
        
        # Scholarship patterns
        elif any(word in message_lower for word in ["scholarship", "financial aid", "grant", "funding", "छात्रवृत्ति", "বৃত্তি"]):
            return {"intent": "scholarship", "confidence": 0.8, "data_needed": ["scholarship"]}
        
        # Hostel/Accommodation patterns
        elif any(word in message_lower for word in ["hostel", "accommodation", "room", "dormitory", "residence", "छात्रावास", "হোস্টেল"]):
            return {"intent": "hostel", "confidence": 0.8, "data_needed": ["hostel"]}
        
        # Schedule patterns
        elif any(word in message_lower for word in ["schedule", "timetable", "class", "time", "exam", "date", "calendar", "समय", "সময়"]):
            return {"intent": "schedule", "confidence": 0.8, "data_needed": ["schedule"]}
        
        # Admission patterns
        elif any(word in message_lower for word in ["admission", "enrollment", "apply", "application", "join", "दाखिला", "ভর্তি"]):
            return {"intent": "admission", "confidence": 0.8, "data_needed": ["admission"]}
        
        # Grade patterns
        elif any(word in message_lower for word in ["grade", "result", "marks", "score", "performance", "परिणाम", "ফলাফল"]):
            return {"intent": "grades", "confidence": 0.8, "data_needed": ["grades"]}
        
        # Library patterns
        elif any(word in message_lower for word in ["library", "book", "borrow", "study", "research", "पुस्तकालय", "লাইব্রেরি"]):
            return {"intent": "library", "confidence": 0.8, "data_needed": ["library"]}
        
        # Complex multi-topic queries
        elif len(message.split()) > 10 and any(word in message_lower for word in ["and", "also", "plus", "additionally"]):
            return {"intent": "complex", "confidence": 0.7, "data_needed": ["multiple"]}
        
        # Help/assistance patterns
        elif any(word in message_lower for word in ["help", "assist", "support", "guide", "information", "info"]):
            return {"intent": "general", "confidence": 0.7, "data_needed": []}
        
        # Thank you patterns
        elif any(word in message_lower for word in ["thank", "thanks", "appreciate", "grateful"]):
            return {"intent": "thanks", "confidence": 0.9, "data_needed": []}
        
        else:
            return {"intent": "general", "confidence": 0.5, "data_needed": []}
    
    async def generate_template_response(self, intent_analysis: Dict, live_data: Dict) -> str:
        """Generate natural, conversational response with proper formatting"""
        intent = intent_analysis.get("intent", "general")
        data = live_data.get("data", {})
        
        if intent == "fees" and "fees" in data:
            fee_info = data["fees"]
            return f"I'd be happy to help you with fee information.\n\nFor the current academic year, here are the details:\n\nSemester Fee: ₹{fee_info.get('semester_fee', '75,000')}\nPayment Due Date: {fee_info.get('due_date', 'July 31, 2024')}\nLate Fee: ₹{fee_info.get('late_fee', '5,000')} (applicable after due date)\n\nPayment Options Available:\nOnline banking and UPI transfers\nCredit and Debit card payments\nBank transfer\nCash payment at accounts office\n\nWould you like more details about any specific payment method or have questions about the fee structure?"
        elif intent == "schedule" and "schedule" in data:
            schedule_info = data["schedule"]
            return f"I can help you with the academic schedule information.\n\nCurrent Semester: {schedule_info.get('current_semester', 'Fall 2024')}\nExam Period: {schedule_info.get('exam_dates', 'December 15-30, 2024')}\nWinter Break: Starts {schedule_info.get('holiday_start', 'December 31, 2024')}\n\nAdditional Information:\nRegular classes are ongoing\nMid-term evaluations completed\nFinal exam schedule will be published soon\n\nWould you like information about specific class timings or any particular subject's schedule?"
        elif intent == "library":
            lib_data = data.get("library", self.get_default_library_data())
            hours = lib_data.get('hours', {})
            if isinstance(hours, dict):
                hours_text = f"Weekdays: {hours.get('weekdays', '8:00 AM - 10:00 PM')}\nWeekends: {hours.get('weekends', '9:00 AM - 6:00 PM')}"
            else:
                hours_text = str(hours)
            return f"Here's comprehensive information about our library services:\n\nOperating Hours:\n{hours_text}\n\nLocation: Central Library Building, Ground Floor\nContact: library@university.edu | Extension: 2345\n\nServices Available:\nBook borrowing and returns\nDigital resources and e-books\nStudy room reservations\nResearch assistance\nPrinting and scanning facilities\n\nIs there a specific book you're looking for, or do you need help with any particular library service?"
        elif intent == "scholarship":
            return "I can help you with scholarship information for students.\n\nAvailable Scholarships:\nMerit-based scholarships for top performers\nNeed-based financial aid for economically disadvantaged students\nInternational student scholarships\nMinority community scholarships\nSports and cultural activity scholarships\n\nEligibility Criteria:\nMinimum 75% marks in previous academic year\nFamily income below specified limits (for need-based)\nValid student enrollment status\nNo pending disciplinary actions\n\nApplication Process:\nFill online scholarship application form\nSubmit required documents (income certificate, mark sheets)\nAttend verification process if selected\nScholarship amount credited to student account\n\nWould you like specific information about any particular scholarship category?"
        elif intent == "hostel":
            return "Here's comprehensive information about hostel accommodation:\n\nHostel Facilities:\nSeparate hostels for boys and girls\nFully furnished rooms with study tables\n24/7 security and warden supervision\nCommon areas for recreation and study\nLaundry and housekeeping services\n\nRoom Types:\nSingle occupancy rooms\nDouble sharing rooms\nTriple sharing rooms\n\nMess Facilities:\nNutritious vegetarian and non-vegetarian meals\nSpecial dietary requirements accommodated\nClean and hygienic kitchen facilities\nFlexible meal timing options\n\nApplication Process:\nFill hostel application form online\nPay hostel fees and security deposit\nSubmit required documents\nRoom allotment based on availability\n\nWould you like information about hostel fees, room availability, or the application procedure?"
        elif intent == "complex":
            return "I understand you have multiple questions. Let me help you with comprehensive information.\n\nFor complex queries involving multiple topics, I can assist you with:\nCombined information about fees, scholarships, and financial aid\nAdmission process along with hostel accommodation details\nAcademic schedules combined with library and facility information\nInternational student guidance covering all university services\n\nTo provide you with the most accurate and detailed information, could you please specify:\nWhich specific topics you'd like me to focus on\nYour current student status (new/existing/international)\nAny particular deadlines or urgent requirements you have\n\nThis will help me give you targeted, comprehensive assistance for all your queries."
        elif intent == "admission":
            adm_data = data.get("admission", self.get_default_admission_data())
            return f"I'm here to assist you with admission information.\n\nImportant Dates:\nApplication Deadline: {adm_data.get('application_deadline', 'June 30, 2024')}\nEntrance Examination: {adm_data.get('entrance_exam', 'July 15, 2024')}\nResults Announcement: {adm_data.get('result_date', 'August 1, 2024')}\n\nRequired Documents:\nAcademic transcripts and certificates\nValid identity proof\nPassport-size photographs\nApplication fee payment receipt\n\nApplication Process:\nOnline application submission\nDocument verification\nEntrance exam (if applicable)\nMerit list publication\n\nWould you like detailed guidance on any specific step of the admission process?"
        elif intent == "greeting":
            import random
            greetings = [
                "Hello! Welcome to our Campus Assistant. I'm here to help you with all your university-related queries.\n\nI can assist you with:\nFee information and payment details\nClass schedules and exam dates\nLibrary services and resources\nAdmission procedures and requirements\nCampus facilities and services\n\nPlease feel free to ask me anything about your university experience. How may I help you today?",
                "Hi there! I'm your Campus Assistant, ready to help with any questions about university services.\n\nI can help you with:\nFee payments and deadlines\nAcademic schedules and exam dates\nLibrary hours and resources\nAdmission information\nGeneral campus information\n\nWhat would you like to know about today?",
                "Good day! I'm here to assist you with all your campus-related queries.\n\nI can provide information about:\nTuition fees and payment options\nClass timetables and important dates\nLibrary services and study resources\nAdmission procedures\nCampus facilities\n\nHow can I help you today?"
            ]
            return random.choice(greetings)
        elif intent == "thanks":
            return "You're most welcome! I'm glad I could help you.\n\nIf you have any more questions about university services, fees, schedules, or anything else, please don't hesitate to ask. I'm here to assist you anytime.\n\nIs there anything else you'd like to know about?"
        else:
            import random
            general_responses = [
                "Thank you for reaching out! I'm your dedicated campus assistant, ready to help with any university-related questions.\n\nI can assist you with:\nFee payment information and deadlines\nAcademic schedules and important dates\nLibrary services and study resources\nAdmission procedures and requirements\nCampus facilities and contact information\nDepartment contacts and office hours\n\nPlease let me know what specific information you're looking for, and I'll provide you with detailed assistance. What would you like to know about?",
                "I'm here to help you with all your campus-related questions and concerns.\n\nI can provide information about:\nTuition fees and payment methods\nClass schedules and exam dates\nLibrary resources and services\nAdmission requirements and deadlines\nCampus facilities and locations\nContact information for departments\n\nWhat specific information can I help you find today?",
                "Hello! I'm your campus assistant, ready to provide information about university services.\n\nI can help you with:\nFee structures and payment options\nAcademic calendars and schedules\nLibrary hours and resources\nAdmission processes and requirements\nCampus services and facilities\nDepartment contact details\n\nHow can I assist you with your university needs today?"
            ]
            return random.choice(general_responses)
    
    async def fallback_response(self, user_message: str, context: Dict) -> Dict[str, Any]:
        """Fallback response when AI fails"""
        return {
            "response": "I apologize, but I'm experiencing technical difficulties. Please try again in a moment or contact the help desk for immediate assistance.",
            "intent": "error",
            "confidence": 0.0,
            "data_sources": [],
            "personalized": False,
            "timestamp": datetime.now().isoformat()
        }
    
    # Default data methods for when APIs are unavailable
    def get_default_fee_data(self) -> Dict:
        return {
            "semester_fee": 50000,
            "due_date": "2024-07-31",
            "late_fee": 5000,
            "payment_methods": ["online", "bank_transfer", "cash"]
        }
    
    def get_default_schedule_data(self) -> Dict:
        return {
            "current_semester": "Fall 2024",
            "exam_dates": "December 15-30, 2024",
            "holiday_start": "December 31, 2024"
        }
    
    def get_default_admission_data(self) -> Dict:
        return {
            "application_deadline": "June 30, 2024",
            "entrance_exam": "July 15, 2024",
            "result_date": "August 1, 2024"
        }
    
    def get_default_library_data(self) -> Dict:
        return {
            "hours": "9:00 AM - 9:00 PM",
            "location": "Central Library Building",
            "contact": "library@university.edu"
        }
    
    def get_multilingual_template_response(self, intent: str, language: str, live_data: Dict) -> str:
        """Get multilingual template responses as fallback"""
        if language == 'hi':  # Hindi
            if intent == "fees":
                return "नमस्ते! मैं आपकी फीस की जानकारी में सहायता कर सकता हूँ।\n\nसेमेस्टर फीस: ₹50,000\nभुगतान की अंतिम तिथि: 31 जुलाई 2024\nविलंब शुल्क: ₹5,000\n\nभुगतान के तरीके: ऑनलाइन, बैंक ट्रांसफर, नकद\n\nक्या आपको कोई और जानकारी चाहिए?"
            elif intent == "library":
                return "पुस्तकालय की जानकारी:\n\nसमय: सुबह 9:00 बजे से रात 9:00 बजे तक\nस्थान: केंद्रीय पुस्तकालय भवन\nसंपर्क: library@university.edu\n\nक्या आपको कोई विशेष पुस्तक चाहिए?"
            else:
                return "नमस्ते! मैं KPRIET का कैंपस असिस्टेंट हूँ। मैं फीस, पुस्तकालय, छात्रवृत्ति और अन्य विश्वविद्यालय सेवाओं के बारे में जानकारी दे सकता हूँ। आप क्या जानना चाहते हैं?"
        
        elif language == 'bn':  # Bengali
            if intent == "fees":
                return "হ্যালো! আমি আপনার ফি সংক্রান্ত তথ্যে সাহায্য করতে পারি।\n\nসেমিস্টার ফি: ₹৫০,০০০\nপেমেন্টের শেষ তারিখ: ৩১ জুলাই ২০২৪\nবিলম্ব ফি: ₹৫,০০০\n\nপেমেন্টের পদ্ধতি: অনলাইন, ব্যাংক ট্রান্সফার, নগদ\n\nআর কোন তথ্য দরকার?"
            elif intent == "library":
                return "লাইব্রেরির তথ্য:\n\nসময়: সকাল ৯টা থেকে রাত ৯টা\nঅবস্থান: কেন্দ্রীয় লাইব্রেরি ভবন\nযোগাযোগ: library@university.edu\n\nকোন বিশেষ বই খুঁজছেন?"
            else:
                return "হ্যালো! আমি KPRIET এর ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি ফি, লাইব্রেরি, বৃত্তি এবং অন্যান্য বিশ্ববিদ্যালয়ের সেবা সম্পর্কে তথ্য দিতে পারি। আপনি কী জানতে চান?"
        
        elif language == 'ta':  # Tamil
            if intent == "fees":
                return "வணக்கம்! நான் உங்கள் கட்டணத் தகவலில் உதவ முடியும்।\n\nசெமஸ்டர் கட்டணம்: ₹50,000\nகட்டணம் செலுத்தும் கடைசி நாள்: ஜூலை 31, 2024\nதாமத கட்டணம்: ₹5,000\n\nகட்டண முறைகள்: ஆன்லைன், வங்கி பரிமாற்றம், பணம்\n\nவேறு ஏதேனும் தகவல் வேண்டுமா?"
            elif intent == "library":
                return "நூலக தகவல்:\n\nநேரம்: காலை 9:00 முதல் இரவு 9:00 வரை\nஇடம்: மத்திய நூலக கட்டிடம்\nதொடர்பு: library@university.edu\n\nஏதேனும் குறிப்பிட்ட புத்தகம் தேவையா?"
            else:
                return "வணக்கம்! நான் KPRIET இன் கேம்பஸ் உதவியாளர். நான் கட்டணம், நூலகம், உதவித்தொகை மற்றும் பிற பல்கலைக்கழக சேவைகள் பற்றிய தகவல்களை வழங்க முடியும். நீங்கள் என்ன தெரிந்து கொள்ள விரும்புகிறீர்கள்?"
        
        else:  # Default English
            return "Hello! I'm KPRIET Campus Assistant. How can I help you today?"
    
    async def generate_multilingual_openai_response(self, user_message: str, intent_analysis: Dict, live_data: Dict, context: Dict, target_language: str) -> str:
        """Generate multilingual response using NVIDIA OpenAI API"""
        try:
            # Language-specific instructions
            language_instructions = {
                'hi': 'Respond in Hindi (हिंदी). Use Devanagari script.',
                'bn': 'Respond in Bengali (বাংলা). Use Bengali script.',
                'ta': 'Respond in Tamil (தமிழ்). Use Tamil script.',
                'ne': 'Respond in Nepali (नेपाली). Use Devanagari script.',
                'en': 'Respond in English.'
            }
            
            language_instruction = language_instructions.get(target_language, 'Respond in English.')
            
            # Prepare university data context
            data_context = ""
            if live_data.get("data"):
                data_context = f"Available University Data: {json.dumps(live_data['data'], indent=2)}"
            
            # Create language-specific prompt with university data
            if target_language == 'hi':
                prompt = f"""आप KPRIET विश्वविद्यालय के कैंपस सहायक हैं। छात्र का प्रश्न: {user_message}

{data_context}

निर्देश:
- हिंदी में उत्तर दें
- उपलब्ध डेटा के आधार पर सटीक जानकारी दें
- व्यावसायिक और सहायक रहें
- स्पष्ट रूप से जानकारी प्रस्तुत करें

विश्वविद्यालय सहायक के रूप में प्राकृतिक उत्तर दें।"""
            elif target_language == 'bn':
                prompt = f"""আপনি KPRIET বিশ্ববিদ্যালয়ের ক্যাম্পাস সহায়ক। ছাত্রের প্রশ্ন: {user_message}

{data_context}

নির্দেশনা:
- বাংলায় উত্তর দিন
- উপলব্ধ তথ্যের ভিত্তিতে সঠিক তথ্য দিন
- পেশাদার এবং সহায়ক হন
- স্পষ্টভাবে তথ্য উপস্থাপন করুন

বিশ্ববিদ্যালয় সহায়ক হিসেবে স্বাভাবিক উত্তর দিন।"""
            elif target_language == 'ta':
                prompt = f"""நீங்கள் KPRIET பல்கலைக்கழகத்தின் கேம்பஸ் உதவியாளர். மாணவரின் கேள்வி: {user_message}

{data_context}

வழிமுறைகள்:
- தமிழில் பதில் அளிக்கவும்
- கிடைக்கும் தரவின் அடிப்படையில் துல்லியமான தகவல் வழங்கவும்
- தொழில்முறை மற்றும் உதவிகரமாக இருங்கள்
- தகவலை தெளிவாக வழங்கவும்

பல்கலைக்கழக உதவியாளராக இயல்பான பதில் அளிக்கவும்."""
            else:
                prompt = f"""You are a professional KPRIET university campus assistant helping students.

Student Query: {user_message}
Intent: {intent_analysis.get('intent', 'general')}
{data_context}

Instructions:
- Provide helpful information about university services
- Use available data to give accurate information
- Be conversational and professional
- Format responses clearly with line breaks
- Don't use markdown formatting

Respond naturally as a university assistant would."""

            # Add timeout for NVIDIA API call
            import asyncio
            completion = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.openai_client.chat.completions.create(
                        model=self.openai_model,
                        messages=[
                            {"role": "system", "content": f"You are a helpful university campus assistant. {language_instruction}"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=512  # Reduced for faster response
                    )
                ),
                timeout=10.0  # 10 second timeout
            )
            
            response = completion.choices[0].message.content.strip()
            logger.info(f"✅ NVIDIA AI multilingual response generated in {target_language}")
            return response
            
        except Exception as e:
            logger.error(f"NVIDIA OpenAI multilingual response failed: {e}")
            return self.get_multilingual_template_response(intent_analysis.get("intent", "general"), target_language, live_data)
    
    async def generate_multilingual_template_response(self, intent_analysis: Dict, live_data: Dict, target_language: str) -> str:
        """Generate multilingual template response as fallback"""
        intent = intent_analysis.get("intent", "general")
        
        # Hindi responses
        if target_language == 'hi':
            if intent in ['greeting', 'general']:
                return "नमस्ते! मैं आपका कैंपस असिस्टेंट हूँ। मैं आपकी निम्नलिखित सेवाओं में सहायता कर सकता हूँ:\n\nफीस की जानकारी और भुगतान विवरण\nकक्षा समय सारणी और परीक्षा तिथियाँ\nपुस्तकालय सेवाएँ और संसाधन\nप्रवेश प्रक्रिया और आवश्यकताएँ\nछात्रवृत्ति की जानकारी\nछात्रावास की सुविधाएँ\n\nआज मैं आपकी कैसे सहायता कर सकता हूँ?"
            elif intent == 'fees':
                return "मुझे फीस की जानकारी में आपकी सहायता करने में खुशी होगी।\n\nवर्तमान शैक्षणिक वर्ष के लिए:\nसेमेस्टर फीस: ₹75,000\nभुगतान की अंतिम तिथि: 31 जुलाई, 2024\nविलंब शुल्क: ₹5,000 (अंतिम तिथि के बाद)\n\nभुगतान के विकल्प:\nऑनलाइन बैंकिंग और UPI\nक्रेडिट/डेबिट कार्ड\nबैंक ट्रांसफर\nखाता कार्यालय में नकद भुगतान\n\nक्या आपको किसी विशिष्ट भुगतान विधि के बारे में और जानकारी चाहिए?"
            elif intent == 'scholarship':
                return "छात्रवृत्ति की जानकारी:\n\nउपलब्ध छात्रवृत्तियाँ:\nमेधावी छात्रों के लिए योग्यता आधारित छात्रवृत्ति\nआर्थिक रूप से कमजोर छात्रों के लिए आवश्यकता आधारित सहायता\nअंतर्राष्ट्रीय छात्रों के लिए विशेष छात्रवृत्ति\nअल्पसंख्यक समुदाय छात्रवृत्ति\n\nपात्रता मानदंड:\nपिछले शैक्षणिक वर्ष में न्यूनतम 75% अंक\nपारिवारिक आय निर्धारित सीमा के अंतर्गत\nवैध छात्र नामांकन स्थिति\n\nक्या आप किसी विशिष्ट छात्रवृत्ति श्रेणी के बारे में जानना चाहते हैं?"
            elif intent == 'library':
                return "पुस्तकालय सेवाओं की जानकारी:\n\nसंचालन समय:\nसप्ताह के दिन: सुबह 8:00 - रात 10:00\nसप्ताहांत: सुबह 9:00 - शाम 6:00\n\nस्थान: केंद्रीय पुस्तकालय भवन, भूतल\nसंपर्क: library@university.edu | एक्सटेंशन: 2345\n\nउपलब्ध सेवाएँ:\nपुस्तक उधार और वापसी\nडिजिटल संसाधन और ई-बुक्स\nअध्ययन कक्ष आरक्षण\nअनुसंधान सहायता\nप्रिंटिंग और स्कैनिंग सुविधाएँ\n\nक्या आप किसी विशिष्ट पुस्तक की खोज कर रहे हैं?"
        
        # Bengali responses
        elif target_language == 'bn':
            if intent in ['greeting', 'general']:
                return "হ্যালো! আমি আপনার ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি নিম্নলিখিত সেবায় আপনাকে সাহায্য করতে পারি:\n\nফি তথ্য এবং পেমেন্ট বিবরণ\nক্লাস সময়সূচী এবং পরীক্ষার তারিখ\nলাইব্রেরি সেবা এবং সম্পদ\nভর্তি প্রক্রিয়া এবং প্রয়োজনীয়তা\nবৃত্তির তথ্য\nহোস্টেল সুবিধা\n\nআজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?"
            elif intent == 'fees':
                return "ফি তথ্যে আপনাকে সাহায্য করতে আমি খুশি।\n\nবর্তমান শিক্ষাবর্ষের জন্য:\nসেমিস্টার ফি: ₹৭৫,০০০\nপেমেন্টের শেষ তারিখ: ৩১ জুলাই, ২০২৪\nবিলম্ব ফি: ₹৫,০০০ (শেষ তারিখের পরে)\n\nপেমেন্ট অপশন:\nঅনলাইন ব্যাংকিং এবং UPI\nক্রেডিট/ডেবিট কার্ড\nব্যাংক ট্রান্সফার\nঅ্যাকাউন্ট অফিসে নগদ পেমেন্ট\n\nআপনার কি কোনো নির্দিষ্ট পেমেন্ট পদ্ধতি সম্পর্কে আরো তথ্য প্রয়োজন?"
            elif intent == 'scholarship':
                return "বৃত্তির তথ্য:\n\nউপলব্ধ বৃত্তি:\nমেধাবী ছাত্রদের জন্য যোগ্যতা ভিত্তিক বৃত্তি\nআর্থিকভাবে দুর্বল ছাত্রদের জন্য প্রয়োজন ভিত্তিক সহায়তা\nআন্তর্জাতিক ছাত্রদের জন্য বিশেষ বৃত্তি\nসংখ্যালঘু সম্প্রদায় বৃত্তি\n\nযোগ্যতার মানদণ্ড:\nপূর্ববর্তী শিক্ষাবর্ষে ন্যূনতম ৭৫% নম্বর\nপারিবারিক আয় নির্ধারিত সীমার মধ্যে\nবৈধ ছাত্র নিবন্ধন অবস্থা\n\nআপনি কি কোনো নির্দিষ্ট বৃত্তি বিভাগ সম্পর্কে জানতে চান?"
        
        # Default to English
        return await self.generate_template_response(intent_analysis, live_data)
    
    async def translate_with_nllb_service(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text using dedicated NLLB service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.nllb_translator_url}/translate",
                    json={
                        "text": text,
                        "source_language": source_lang,
                        "target_language": target_lang
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["translated_text"]
                else:
                    logger.error(f"NLLB service error: {response.status_code}")
                    raise Exception(f"Translation service error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"NLLB service connection failed: {e}")
            raise e
    
    def get_multilingual_fallback(self, language: str, intent_analysis: Dict) -> str:
        """High-quality multilingual fallback responses"""
        intent = intent_analysis.get("intent", "general")
        
        fallbacks = {
            'hi': {
                'greeting': "नमस्ते! मैं आपका कैंपस असिस्टेंट हूँ। मैं आपकी विश्वविद्यालय संबंधी सभी जानकारी में सहायता कर सकता हूँ। आज मैं आपकी कैसे सहायता कर सकता हूँ?",
                'fees': "मुझे फीस की जानकारी में आपकी सहायता करने में खुशी होगी।\n\nवर्तमान शैक्षणिक वर्ष के लिए:\n• सेमेस्टर फीस: ₹75,000\n• भुगतान की अंतिम तिथि: 31 जुलाई, 2024\n• विलंब शुल्क: ₹5,000\n\nभुगतान के विकल्प: ऑनलाइन बैंकिंग, UPI, कार्ड भुगतान\n\nक्या आपको और जानकारी चाहिए?",
                'general': "मैं आपका कैंपस असिस्टेंट हूँ। मैं फीस, समय सारणी, पुस्तकालय और प्रवेश की जानकारी में सहायता कर सकता हूँ।"
            },
            'bn': {
                'greeting': "হ্যালো! আমি আপনার ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি আপনার বিশ্ববিদ্যালয় সম্পর্কিত সমস্ত তথ্যে সহায়তা করতে পারি। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
                'fees': "ফি তথ্যে আপনাকে সাহায্য করতে আমি খুশি।\n\nবর্তমান শিক্ষাবর্ষের জন্য:\n• সেমিস্টার ফি: ₹৭৫,০০০\n• পেমেন্টের শেষ তারিখ: ৩১ জুলাই, ২০২৪\n• বিলম্ব ফি: ₹৫,০০০\n\nপেমেন্ট অপশন: অনলাইন ব্যাংকিং, UPI, কার্ড পেমেন্ট\n\nআরো তথ্য প্রয়োজন?",
                'general': "আমি আপনার ক্যাম্পাস অ্যাসিস্ট্যান্ট। আমি ফি, সময়সূচী, লাইব্রেরি এবং ভর্তির তথ্যে সাহায্য করতে পারি।"
            },
            'ta': {
                'greeting': "வணக்கம்! நான் உங்கள் கேம்பஸ் உதவியாளர். நான் உங்கள் பல்கலைக்கழகம் தொடர்பான அனைத்து தகவல்களிலும் உதவ முடியும். இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?",
                'fees': "கட்டண தகவல்களில் உங்களுக்கு உதவ மகிழ்ச்சி।\n\nதற்போதைய கல்வியாண்டுக்கு:\n• செமஸ்டர் கட்டணம்: ₹75,000\n• கட்டண கடைசி தேதி: ஜூலை 31, 2024\n• தாமத கட்டணம்: ₹5,000\n\nகட்டண விருப்பங்கள்: ஆன்லைன் வங்கி, UPI, கார்டு பேமெண்ட்\n\nமேலும் தகவல் தேவையா?",
                'general': "நான் உங்கள் கேம்பஸ் உதவியாளர். நான் கட்டணம், நேர அட்டவணை, நூலகம் மற்றும் சேர்க்கை தகவல்களில் உதவ முடியும்।"
            },
            'te': {
                'greeting': "నమస్కారం! నేను మీ క్యాంపస్ అసిస్టెంట్. నేను మీ విశ్వవిద్యాలయం సంబంధిత అన్ని సమాచారంలో సహాయం చేయగలను. ఈరోజు నేను మీకు ఎలా సహాయం చేయగలను?",
                'fees': "ఫీజు సమాచారంలో మీకు సహాయం చేయడంలో సంతోషం।\n\nప్రస్తుత విద్యా సంవత్సరానికి:\n• సెమిస్టర్ ఫీజు: ₹75,000\n• చెల్లింపు చివరి తేదీ: జూలై 31, 2024\n• ఆలస్య ఫీజు: ₹5,000\n\nచెల్లింపు ఎంపికలు: ఆన్‌లైన్ బ్యాంకింగ్, UPI, కార్డు పేమెంట్\n\nమరింత సమాచారం కావాలా?",
                'general': "నేను మీ క్యాంపస్ అసిస్టెంట్. నేను ఫీజు, టైమ్ టేబుల్, లైబ్రేరీ మరియు అడ్మిషన్ సమాచారంలో సహాయం చేయగలను।"
            },
            'kn': {
                'greeting': "ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಕ್ಯಾಂಪಸ್ ಅಸಿಸ್ಟೆಂಟ್. ನಾನು ನಿಮ್ಮ ವಿಶ್ವವಿದ್ಯಾಲಯ ಸಂಬಂಧಿತ ಎಲ್ಲಾ ಮಾಹಿತಿಯಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು. ಇಂದು ನಾನು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
                'fees': "ಶುಲ್ಕ ಮಾಹಿತಿಯಲ್ಲಿ ನಿಮಗೆ ಸಹಾಯ ಮಾಡಲು ಸಂತೋಷ।\n\nಪ್ರಸ್ತುತ ಶೈಕ್ಷಣಿಕ ವರ್ಷಕ್ಕೆ:\n• ಸೆಮಿಸ್ಟರ್ ಶುಲ್ಕ: ₹75,000\n• ಪಾವತಿ ಕೊನೆಯ ದಿನಾಂಕ: ಜುಲೈ 31, 2024\n• ವಿಳಂಬ ಶುಲ್ಕ: ₹5,000\n\nಪಾವತಿ ಆಯ್ಕೆಗಳು: ಆನ್‌ಲೈನ್ ಬ್ಯಾಂಕಿಂಗ್, UPI, ಕಾರ್ಡ್ ಪೇಮೆಂಟ್\n\nಹೆಚ್ಚಿನ ಮಾಹಿತಿ ಬೇಕೇ?",
                'general': "ನಾನು ನಿಮ್ಮ ಕ್ಯಾಂಪಸ್ ಅಸಿಸ್ಟೆಂಟ್. ನಾನು ಶುಲ್ಕ, ಸಮಯ ಕೋಷ್ಟಕ, ಗ್ರಂಥಾಲಯ ಮತ್ತು ಪ್ರವೇಶ ಮಾಹಿತಿಯಲ್ಲಿ ಸಹಾಯ ಮಾಡಬಹುದು।"
            },
            'ml': {
                'greeting': "നമസ്കാരം! ഞാൻ നിങ്ങളുടെ കാമ്പസ് അസിസ്റ്റന്റ്. എനിക്ക് നിങ്ങളുടെ സർവകലാശാല സംബന്ധിച്ച എല്ലാ വിവരങ്ങളിലും സഹായിക്കാൻ കഴിയും. ഇന്ന് ഞാൻ നിങ്ങളെ എങ്ങനെ സഹായിക്കാം?",
                'fees': "ഫീസ് വിവരങ്ങളിൽ നിങ്ങളെ സഹായിക്കാൻ സന്തോഷം।\n\nനിലവിലെ അക്കാദമിക് വർഷത്തിന്:\n• സെമസ്റ്റർ ഫീസ്: ₹75,000\n• പേയ്‌മെന്റ് അവസാന തീയതി: ജൂലൈ 31, 2024\n• വൈകി ഫീസ്: ₹5,000\n\nപേയ്‌മെന്റ് ഓപ്ഷനുകൾ: ഓൺലൈൻ ബാങ്കിംഗ്, UPI, കാർഡ് പേയ്‌മെന്റ്\n\nകൂടുതൽ വിവരങ്ങൾ വേണോ?",
                'general': "ഞാൻ നിങ്ങളുടെ കാമ്പസ് അസിസ്റ്റന്റ്. എനിക്ക് ഫീസ്, ടൈം ടേബിൾ, ലൈബ്രറി, പ്രവേശന വിവരങ്ങളിൽ സഹായിക്കാൻ കഴിയും।"
            }
        }
        
        lang_responses = fallbacks.get(language, {})
        return lang_responses.get(intent, lang_responses.get('general', "Hello! I'm your Campus Assistant. How can I help you today?"))
