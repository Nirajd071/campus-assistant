"""
Multilingual Campus Assistant - NLP Engine
Main FastAPI application for natural language processing
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import logging

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from services.language_detector import LanguageDetector
from services.intent_classifier import IntentClassifier
from services.context_manager import ContextManager
from services.response_generator import ResponseGenerator
from services.ai_service import RealTimeAIService
from utils.logger import setup_logger
from config.settings import Settings

# Initialize settings and logger
settings = Settings()
logger = setup_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Campus Assistant NLP Engine",
    description="Multilingual Natural Language Processing Engine for Campus Assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
language_detector: Optional[LanguageDetector] = None
intent_classifier: Optional[IntentClassifier] = None
context_manager: Optional[ContextManager] = None
response_generator: Optional[ResponseGenerator] = None
ai_service: Optional[RealTimeAIService] = None

# Pydantic models
class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: str = Field(..., description="Session identifier")
    language: Optional[str] = Field(None, description="Detected or preferred language")
    platform: str = Field(default="web", description="Platform (web, whatsapp, telegram)")

class ChatResponse(BaseModel):
    response: str = Field(..., description="Bot response")
    language: str = Field(..., description="Response language")
    intent: str = Field(..., description="Detected intent")
    confidence: float = Field(..., description="Confidence score")
    context: Dict[str, Any] = Field(default_factory=dict, description="Conversation context")
    escalate_to_human: bool = Field(default=False, description="Whether to escalate to human")
    response_time_ms: int = Field(..., description="Processing time in milliseconds")

class LanguageDetectionRequest(BaseModel):
    text: str = Field(..., description="Text to detect language for")

class LanguageDetectionResponse(BaseModel):
    language: str = Field(..., description="Detected language code")
    confidence: float = Field(..., description="Detection confidence")
    supported_languages: List[str] = Field(..., description="List of supported languages")

class IntentRequest(BaseModel):
    text: str = Field(..., description="Text to classify intent for")
    language: str = Field(default="en", description="Text language")

class IntentResponse(BaseModel):
    intent: str = Field(..., description="Classified intent")
    confidence: float = Field(..., description="Classification confidence")
    entities: Dict[str, Any] = Field(default_factory=dict, description="Extracted entities")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    uptime: str = Field(..., description="Service uptime")
    services: Dict[str, str] = Field(..., description="Service component status")

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize all NLP services on startup"""
    global language_detector, intent_classifier, context_manager, response_generator, ai_service
    
    logger.info("🚀 Starting Campus Assistant NLP Engine...")
    
    try:
        # Initialize language detector
        logger.info("Initializing Language Detector...")
        language_detector = LanguageDetector()
        await language_detector.initialize()
        
        # Initialize intent classifier
        logger.info("Initializing Intent Classifier...")
        intent_classifier = IntentClassifier()
        await intent_classifier.initialize()
        
        # Initialize context manager
        logger.info("Initializing Context Manager...")
        context_manager = ContextManager()
        await context_manager.initialize()
        
        # Initialize response generator
        logger.info("Initializing Response Generator...")
        response_generator = ResponseGenerator()
        await response_generator.initialize()
        
        # Initialize AI service
        logger.info("Initializing AI Service...")
        ai_service = RealTimeAIService()
        
        logger.info("✅ All NLP services initialized successfully!")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize NLP services: {str(e)}")
        raise

# Dependency to get services
async def get_services():
    """Dependency to ensure services are initialized"""
    if not all([language_detector, intent_classifier, context_manager, response_generator, ai_service]):
        raise HTTPException(status_code=503, detail="NLP services not initialized")
    
    return {
        "language_detector": language_detector,
        "intent_classifier": intent_classifier,
        "context_manager": context_manager,
        "response_generator": response_generator,
        "ai_service": ai_service
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    start_time = getattr(app.state, 'start_time', datetime.now())
    uptime = str(datetime.now() - start_time)
    
    services_status = {
        "language_detector": "healthy" if language_detector else "not_initialized",
        "intent_classifier": "healthy" if intent_classifier else "not_initialized",
        "context_manager": "healthy" if context_manager else "not_initialized",
        "response_generator": "healthy" if response_generator else "not_initialized"
    }
    
    overall_status = "healthy" if all(status == "healthy" for status in services_status.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        uptime=uptime,
        services=services_status
    )

# Language detection endpoint
@app.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: LanguageDetectionRequest,
    services: Dict = Depends(get_services)
):
    """Detect language of input text"""
    try:
        start_time = datetime.now()
        
        detector = services["language_detector"]
        result = await detector.detect_language(request.text)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Language detection completed in {processing_time:.2f}ms")
        
        return LanguageDetectionResponse(
            language=result["language"],
            confidence=result["confidence"],
            supported_languages=detector.supported_languages
        )
        
    except Exception as e:
        logger.error(f"Language detection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Language detection failed: {str(e)}")

# Intent classification endpoint
@app.post("/classify-intent", response_model=IntentResponse)
async def classify_intent(
    request: IntentRequest,
    services: Dict = Depends(get_services)
):
    """Classify intent of input text"""
    try:
        start_time = datetime.now()
        
        classifier = services["intent_classifier"]
        result = await classifier.classify_intent(request.text, request.language)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.info(f"Intent classification completed in {processing_time:.2f}ms")
        
        return IntentResponse(
            intent=result["intent"],
            confidence=result["confidence"],
            entities=result.get("entities", {})
        )
        
    except Exception as e:
        logger.error(f"Intent classification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intent classification failed: {str(e)}")

# Main chat processing endpoint
@app.post("/chat", response_model=ChatResponse)
async def process_chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    services: Dict = Depends(get_services)
):
    """Process chat message and generate response"""
    try:
        start_time = datetime.now()
        
        # Extract services
        detector = services["language_detector"]
        context_mgr = services["context_manager"]
        ai_service = services["ai_service"]
        
        # Step 1: Detect language if not provided
        if not request.language:
            lang_result = await detector.detect_language(request.message)
            detected_language = lang_result["language"]
        else:
            detected_language = request.language
        
        logger.info(f"Processing message in language: {detected_language}")
        
        # Step 2: Get conversation context
        context = await context_mgr.get_context(request.session_id)
        
        # Step 3: Use Real-time AI Service for intelligent response
        ai_response = await ai_service.get_multilingual_response(
            user_message=request.message,
            context=context,
            student_id=getattr(request, 'user_id', None),
            preferred_language=detected_language
        )
        
        logger.info(f"AI Response generated: {ai_response['intent']} (confidence: {ai_response['confidence']:.2f})")
        
        # Use the AI service response directly (it handles NLLB translation)
        final_response = ai_response["response"]
        logger.info(f"Final response length: {len(final_response) if final_response else 0}")
        
        # Debug: Check if response is empty
        if not final_response or final_response.strip() == "":
            logger.error(f"Empty response detected! AI Response: {ai_response}")
            final_response = "I apologize, but I encountered an issue generating a response. Please try again."
        
        # Step 5: Update context with AI response
        await context_mgr.update_context(
            request.session_id,
            {
                "user_message": request.message,
                "language": detected_language,
                "intent": ai_response["intent"],
                "confidence": ai_response["confidence"],
                "ai_response": final_response,
                "data_sources": ai_response.get("data_sources", []),
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Log conversation for analytics (background task)
        background_tasks.add_task(
            log_conversation,
            request.session_id,
            request.user_id,
            request.message,
            ai_response["response"],
            detected_language,
            ai_response["intent"],
            ai_response["confidence"],
            processing_time,
            request.platform
        )
        
        logger.info(f"Chat processing completed in {processing_time}ms")
        
        return ChatResponse(
            response=final_response,
            language=detected_language,
            intent=ai_response["intent"],
            confidence=ai_response["confidence"],
            context=context,
            escalate_to_human=ai_response.get("escalate_to_human", False),
            response_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

# Background task for logging
async def log_conversation(
    session_id: str,
    user_id: Optional[str],
    user_message: str,
    bot_response: str,
    language: str,
    intent: str,
    confidence: float,
    processing_time: int,
    platform: str
):
    """Log conversation data for analytics"""
    try:
        log_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_message": user_message,
            "bot_response": bot_response,
            "language": language,
            "intent": intent,
            "confidence": confidence,
            "processing_time_ms": processing_time,
            "platform": platform,
            "timestamp": datetime.now().isoformat()
        }
        
        # Log to file (in production, send to analytics service)
        logger.info(f"CONVERSATION_LOG: {json.dumps(log_data)}")
        
    except Exception as e:
        logger.error(f"Failed to log conversation: {str(e)}")

# Context management endpoints
@app.get("/context/{session_id}")
async def get_session_context(
    session_id: str,
    services: Dict = Depends(get_services)
):
    """Get conversation context for a session"""
    try:
        context_mgr = services["context_manager"]
        context = await context_mgr.get_context(session_id)
        return {"session_id": session_id, "context": context}
        
    except Exception as e:
        logger.error(f"Context retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context retrieval failed: {str(e)}")

@app.delete("/context/{session_id}")
async def clear_session_context(
    session_id: str,
    services: Dict = Depends(get_services)
):
    """Clear conversation context for a session"""
    try:
        context_mgr = services["context_manager"]
        await context_mgr.clear_context(session_id)
        return {"message": f"Context cleared for session {session_id}"}
        
    except Exception as e:
        logger.error(f"Context clearing error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Context clearing failed: {str(e)}")

# Metrics endpoint
@app.get("/metrics")
async def get_metrics():
    """Get service metrics"""
    try:
        # In production, integrate with Prometheus or similar
        metrics = {
            "total_requests": getattr(app.state, 'total_requests', 0),
            "successful_requests": getattr(app.state, 'successful_requests', 0),
            "failed_requests": getattr(app.state, 'failed_requests', 0),
            "avg_response_time_ms": getattr(app.state, 'avg_response_time', 0),
            "supported_languages": language_detector.supported_languages if language_detector else [],
            "available_intents": intent_classifier.available_intents if intent_classifier else []
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics retrieval error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics retrieval failed: {str(e)}")

# Middleware to track requests
@app.middleware("http")
async def track_requests(request, call_next):
    """Middleware to track request metrics"""
    start_time = datetime.now()
    
    # Increment total requests
    app.state.total_requests = getattr(app.state, 'total_requests', 0) + 1
    
    try:
        response = await call_next(request)
        
        # Track successful requests
        if response.status_code < 400:
            app.state.successful_requests = getattr(app.state, 'successful_requests', 0) + 1
        else:
            app.state.failed_requests = getattr(app.state, 'failed_requests', 0) + 1
            
        # Track response time
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        current_avg = getattr(app.state, 'avg_response_time', 0)
        total_requests = app.state.total_requests
        app.state.avg_response_time = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        
        return response
        
    except Exception as e:
        app.state.failed_requests = getattr(app.state, 'failed_requests', 0) + 1
        raise

if __name__ == "__main__":
    # Set start time
    app.state.start_time = datetime.now()
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("NLP_ENGINE_PORT", 8001)),
        reload=True,
        log_level="info"
    )
