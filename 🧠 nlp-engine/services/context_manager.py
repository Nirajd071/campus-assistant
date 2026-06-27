"""
Context Management Service
Handles conversation context and session management for multi-turn conversations
"""

import asyncio
import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid

try:
    import redis.asyncio as redis
except ImportError:
    redis = None

from utils.logger import setup_logger

logger = setup_logger(__name__)

class ContextManager:
    """
    Manages conversation context for multi-turn conversations
    
    Features:
    - Session-based context storage
    - Conversation history tracking
    - Context expiration and cleanup
    - Redis-based persistence
    - Context summarization for long conversations
    """
    
    def __init__(self, redis_url: str = None):
        # Build the Redis URL from discrete env vars (as provided by
        # docker-compose) or an explicit REDIS_URL, falling back to localhost.
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            host = os.getenv("REDIS_HOST", "localhost")
            port = os.getenv("REDIS_PORT", "6379")
            password = os.getenv("REDIS_PASSWORD")
            if password:
                redis_url = f"redis://:{password}@{host}:{port}"
            else:
                redis_url = f"redis://{host}:{port}"
        self.redis_url = redis_url
        self.redis_client = None
        self.session_timeout = timedelta(minutes=30)  # 30 minutes default
        self.max_context_turns = 10  # Maximum conversation turns to keep
        self.is_initialized = False
        
        # In-memory fallback for when Redis is not available
        self.memory_store = {}
        
    async def initialize(self):
        """Initialize Redis connection and context manager"""
        try:
            logger.info("Initializing Context Manager...")
            
            if redis:
                try:
                    self.redis_client = redis.from_url(self.redis_url)
                    # Test connection
                    await self.redis_client.ping()
                    logger.info("Redis connection established")
                except Exception as e:
                    logger.warning(f"Redis connection failed, using in-memory storage: {e}")
                    self.redis_client = None
            else:
                logger.warning("Redis not available, using in-memory storage")
            
            self.is_initialized = True
            logger.info("Context Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Context Manager: {e}")
            raise
    
    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """Get conversation context for a session"""
        if not self.is_initialized:
            await self.initialize()
        
        try:
            if self.redis_client:
                # Get from Redis
                context_data = await self.redis_client.get(f"context:{session_id}")
                if context_data:
                    context = json.loads(context_data)
                    # Check if context has expired
                    if self._is_context_expired(context):
                        await self.clear_context(session_id)
                        return self._create_empty_context(session_id)
                    return context
            else:
                # Get from memory
                context = self.memory_store.get(session_id)
                if context and not self._is_context_expired(context):
                    return context
                elif context:
                    # Remove expired context
                    del self.memory_store[session_id]
            
            # Return empty context if not found or expired
            return self._create_empty_context(session_id)
            
        except Exception as e:
            logger.error(f"Failed to get context for session {session_id}: {e}")
            return self._create_empty_context(session_id)
    
    async def update_context(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update conversation context with new data"""
        try:
            # Get current context
            context = await self.get_context(session_id)
            
            # Update context with new data
            context["last_updated"] = datetime.now().isoformat()
            context["turn_count"] += 1
            
            # Add to conversation history
            if "conversation_history" not in context:
                context["conversation_history"] = []
            
            # Create conversation turn
            turn = {
                "turn_id": len(context["conversation_history"]) + 1,
                "timestamp": datetime.now().isoformat(),
                **update_data
            }
            
            context["conversation_history"].append(turn)
            
            # Maintain context size limit
            if len(context["conversation_history"]) > self.max_context_turns:
                # Keep recent turns and summarize older ones
                context = await self._summarize_context(context)
            
            # Update current state
            if "user_message" in update_data:
                context["last_user_message"] = update_data["user_message"]
            if "bot_response" in update_data:
                context["last_bot_response"] = update_data["bot_response"]
            if "intent" in update_data:
                context["last_intent"] = update_data["intent"]
            if "language" in update_data:
                context["language"] = update_data["language"]
            
            # Store updated context
            await self._store_context(session_id, context)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update context for session {session_id}: {e}")
            return False
    
    async def clear_context(self, session_id: str) -> bool:
        """Clear conversation context for a session"""
        try:
            if self.redis_client:
                await self.redis_client.delete(f"context:{session_id}")
            else:
                self.memory_store.pop(session_id, None)
            
            logger.info(f"Context cleared for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear context for session {session_id}: {e}")
            return False
    
    def _create_empty_context(self, session_id: str) -> Dict[str, Any]:
        """Create an empty context for a new session"""
        return {
            "session_id": session_id,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "turn_count": 0,
            "language": "en",
            "conversation_history": [],
            "last_user_message": None,
            "last_bot_response": None,
            "last_intent": None,
            "escalated_to_human": False,
            "user_preferences": {},
            "context_summary": ""
        }
    
    async def _store_context(self, session_id: str, context: Dict[str, Any]) -> bool:
        """Store context in Redis or memory"""
        try:
            if self.redis_client:
                # Store in Redis with expiration
                context_json = json.dumps(context, default=str)
                await self.redis_client.setex(
                    f"context:{session_id}",
                    int(self.session_timeout.total_seconds()),
                    context_json
                )
            else:
                # Store in memory
                self.memory_store[session_id] = context
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store context for session {session_id}: {e}")
            return False
    
    def _is_context_expired(self, context: Dict[str, Any]) -> bool:
        """Check if context has expired"""
        try:
            last_updated = datetime.fromisoformat(context.get("last_updated", ""))
            return datetime.now() - last_updated > self.session_timeout
        except (ValueError, TypeError):
            return True
    
    async def _summarize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize context when it gets too long"""
        try:
            history = context.get("conversation_history", [])
            
            if len(history) <= self.max_context_turns:
                return context
            
            # Keep recent turns
            recent_turns = history[-self.max_context_turns//2:]
            
            # Summarize older turns
            older_turns = history[:-self.max_context_turns//2]
            
            # Create summary of older turns
            topics = set()
            intents = set()
            
            for turn in older_turns:
                if "intent" in turn:
                    intents.add(turn["intent"])
                if "user_message" in turn:
                    # Extract key topics (simple keyword extraction)
                    words = turn["user_message"].lower().split()
                    topics.update([w for w in words if len(w) > 4])
            
            summary = {
                "summarized_turns": len(older_turns),
                "topics_discussed": list(topics)[:10],  # Keep top 10 topics
                "intents_used": list(intents),
                "summary_created_at": datetime.now().isoformat()
            }
            
            # Update context
            context["conversation_history"] = recent_turns
            context["context_summary"] = summary
            
            logger.info(f"Summarized {len(older_turns)} older turns for session {context['session_id']}")
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to summarize context: {e}")
            return context
