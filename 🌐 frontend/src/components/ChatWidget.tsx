import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  Avatar,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Fab,
  Collapse,
  AppBar,
  Toolbar,
  Badge,
} from '@mui/material';
import {
  Send as SendIcon,
  Chat as ChatIcon,
  Close as CloseIcon,
  Translate as TranslateIcon,
  Person as PersonIcon,
  SmartToy as BotIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useChat } from '../contexts/ChatContext';
import { useAuth } from '../contexts/AuthContext';
import MessageBubble from './MessageBubble';
import TypingIndicator from './TypingIndicator';
import QuickActions from './QuickActions';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  language: string;
  intent?: string;
  confidence?: number;
}

const ChatWidget: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const { sendMessage, messages, isLoading, sessionId } = useChat();
  
  const [isOpen, setIsOpen] = useState(false);
  const [inputMessage, setInputMessage] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState(i18n.language);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const supportedLanguages = [
    { code: 'en', name: 'English', nativeName: 'English' },
    { code: 'hi', name: 'Hindi', nativeName: 'हिंदी' },
    { code: 'bn', name: 'Bengali', nativeName: 'বাংলা' },
    { code: 'ta', name: 'Tamil', nativeName: 'தமிழ்' },
    { code: 'mr', name: 'Marathi', nativeName: 'मराठी' },
  ];

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    i18n.changeLanguage(selectedLanguage);
  }, [selectedLanguage, i18n]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const messageData = {
      content: inputMessage,
      language: selectedLanguage,
      sessionId,
      userId: user?.id,
    };

    await sendMessage(messageData);
    setInputMessage('');
  };

  const handleKeyPress = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  const handleLanguageChange = (language: string) => {
    setSelectedLanguage(language);
  };

  const handleQuickAction = (action: string) => {
    const quickMessages = {
      fees: t('quickActions.fees'),
      scholarships: t('quickActions.scholarships'),
      timetable: t('quickActions.timetable'),
      facilities: t('quickActions.facilities'),
    };

    setInputMessage(quickMessages[action as keyof typeof quickMessages] || action);
  };

  return (
    <>
      {/* Chat Fab Button */}
      <Fab
        color="primary"
        aria-label="chat"
        sx={{
          position: 'fixed',
          bottom: 20,
          right: 20,
          zIndex: 1000,
        }}
        onClick={() => setIsOpen(!isOpen)}
      >
        <Badge badgeContent={messages.length > 0 ? messages.length : 0} color="secondary">
          {isOpen ? <CloseIcon /> : <ChatIcon />}
        </Badge>
      </Fab>

      {/* Chat Widget */}
      <Collapse in={isOpen}>
        <Paper
          elevation={8}
          sx={{
            position: 'fixed',
            bottom: 90,
            right: 20,
            width: 380,
            height: 600,
            display: 'flex',
            flexDirection: 'column',
            zIndex: 999,
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          {/* Header */}
          <AppBar position="static" elevation={0}>
            <Toolbar variant="dense">
              <BotIcon sx={{ mr: 1 }} />
              <Typography variant="h6" sx={{ flexGrow: 1 }}>
                {t('chatWidget.title')}
              </Typography>
              
              {/* Language Selector */}
              <FormControl size="small" sx={{ minWidth: 80, mr: 1 }}>
                <Select
                  value={selectedLanguage}
                  onChange={(e) => handleLanguageChange(e.target.value)}
                  sx={{ color: 'white', '& .MuiSvgIcon-root': { color: 'white' } }}
                >
                  {supportedLanguages.map((lang) => (
                    <MenuItem key={lang.code} value={lang.code}>
                      {lang.nativeName}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <IconButton
                color="inherit"
                onClick={() => setIsOpen(false)}
                size="small"
              >
                <CloseIcon />
              </IconButton>
            </Toolbar>
          </AppBar>

          {/* Messages Area */}
          <Box
            sx={{
              flexGrow: 1,
              overflow: 'auto',
              p: 1,
              backgroundColor: '#f5f5f5',
            }}
          >
            {messages.length === 0 && (
              <Box sx={{ textAlign: 'center', mt: 4 }}>
                <BotIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                <Typography variant="body1" color="textSecondary">
                  {t('chatWidget.welcome')}
                </Typography>
                <QuickActions onActionClick={handleQuickAction} />
              </Box>
            )}

            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                isUser={message.sender === 'user'}
              />
            ))}

            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </Box>

          {/* Input Area */}
          <Box sx={{ p: 2, backgroundColor: 'white', borderTop: 1, borderColor: 'divider' }}>
            <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                fullWidth
                multiline
                maxRows={3}
                placeholder={t('chatWidget.inputPlaceholder')}
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                variant="outlined"
                size="small"
                disabled={isLoading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 3,
                  },
                }}
              />
              <IconButton
                color="primary"
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isLoading}
                sx={{
                  backgroundColor: 'primary.main',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: 'primary.dark',
                  },
                  '&:disabled': {
                    backgroundColor: 'grey.300',
                  },
                }}
              >
                <SendIcon />
              </IconButton>
            </Box>

            {/* Status Indicator */}
            <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Typography variant="caption" color="textSecondary">
                {user ? `${t('chatWidget.loggedInAs')} ${user.username}` : t('chatWidget.anonymous')}
              </Typography>
              <Chip
                size="small"
                label={supportedLanguages.find(l => l.code === selectedLanguage)?.nativeName}
                icon={<TranslateIcon />}
                variant="outlined"
              />
            </Box>
          </Box>
        </Paper>
      </Collapse>
    </>
  );
};

export default ChatWidget;
