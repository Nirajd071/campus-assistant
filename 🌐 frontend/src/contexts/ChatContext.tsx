import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { v4 as uuidv4 } from 'uuid';
import axios from 'axios';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  language: string;
  intent?: string;
  confidence?: number;
}

interface ChatContextType {
  messages: Message[];
  isLoading: boolean;
  sessionId: string;
  sendMessage: (messageData: {
    content: string;
    language: string;
    sessionId: string;
    userId?: string;
  }) => Promise<void>;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
};

interface ChatProviderProps {
  children: ReactNode;
}

export const ChatProvider: React.FC<ChatProviderProps> = ({ children }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => uuidv4());

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3007';
  const NLP_API_URL = process.env.REACT_APP_NLP_API_URL || 'http://localhost:8001';

  const sendMessage = useCallback(async (messageData: {
    content: string;
    language: string;
    sessionId: string;
    userId?: string;
  }) => {
    const userMessage: Message = {
      id: uuidv4(),
      content: messageData.content,
      sender: 'user',
      timestamp: new Date(),
      language: messageData.language,
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send to NLP engine
      const nlpResponse = await axios.post(`${NLP_API_URL}/chat`, {
        message: messageData.content,
        user_id: messageData.userId,
        session_id: messageData.sessionId,
        language: messageData.language,
        platform: 'web',
      });

      const { response, language, intent, confidence, escalate_to_human } = nlpResponse.data;

      // Create bot response message
      const botMessage: Message = {
        id: uuidv4(),
        content: response,
        sender: 'bot',
        timestamp: new Date(),
        language: language,
        intent: intent,
        confidence: confidence,
      };

      // Add bot message
      setMessages(prev => [...prev, botMessage]);

      // Log conversation to backend
      try {
        await axios.post(`${API_BASE_URL}/api/conversations`, {
          session_id: messageData.sessionId,
          user_id: messageData.userId,
          message_type: 'user',
          content: messageData.content,
          language: messageData.language,
          intent: intent,
          confidence: confidence,
        });

        await axios.post(`${API_BASE_URL}/api/conversations`, {
          session_id: messageData.sessionId,
          user_id: messageData.userId,
          message_type: 'bot',
          content: response,
          language: language,
          intent: intent,
          confidence: confidence,
          escalated_to_human: escalate_to_human,
        });
      } catch (loggingError) {
        console.warn('Failed to log conversation:', loggingError);
      }

      // Handle human escalation
      if (escalate_to_human) {
        const escalationMessage: Message = {
          id: uuidv4(),
          content: 'A human staff member will be with you shortly. Please wait while we connect you.',
          sender: 'bot',
          timestamp: new Date(),
          language: language,
          intent: 'escalation',
          confidence: 1.0,
        };

        setTimeout(() => {
          setMessages(prev => [...prev, escalationMessage]);
        }, 1000);
      }

    } catch (error) {
      console.error('Failed to send message:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: uuidv4(),
        content: 'Sorry, I encountered an error. Please try again later.',
        sender: 'bot',
        timestamp: new Date(),
        language: messageData.language,
        intent: 'error',
        confidence: 0.0,
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE_URL, NLP_API_URL]);

  const clearChat = useCallback(() => {
    setMessages([]);
  }, []);

  const value: ChatContextType = {
    messages,
    isLoading,
    sessionId,
    sendMessage,
    clearChat,
  };

  return (
    <ChatContext.Provider value={value}>
      {children}
    </ChatContext.Provider>
  );
};

export default ChatContext;
