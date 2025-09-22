import React from 'react';
import {
  Box,
  Paper,
  Typography,
  Avatar,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Person as PersonIcon,
  SmartToy as BotIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  ContentCopy as CopyIcon,
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  language: string;
  intent?: string;
  confidence?: number;
}

interface MessageBubbleProps {
  message: Message;
  isUser: boolean;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message, isUser }) => {
  const { t } = useTranslation();

  const handleCopyMessage = () => {
    navigator.clipboard.writeText(message.content);
  };

  const handleFeedback = (positive: boolean) => {
    // TODO: Implement feedback API call
    console.log(`Feedback for message ${message.id}: ${positive ? 'positive' : 'negative'}`);
  };

  const formatTime = (timestamp: Date) => {
    return new Intl.DateTimeFormat('default', {
      hour: '2-digit',
      minute: '2-digit',
    }).format(timestamp);
  };

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        alignItems: 'flex-start',
        gap: 1,
      }}
    >
      {!isUser && (
        <Avatar
          sx={{
            width: 32,
            height: 32,
            backgroundColor: 'primary.main',
          }}
        >
          <BotIcon fontSize="small" />
        </Avatar>
      )}

      <Box sx={{ maxWidth: '75%' }}>
        <Paper
          elevation={1}
          sx={{
            p: 2,
            backgroundColor: isUser ? 'primary.main' : 'white',
            color: isUser ? 'white' : 'text.primary',
            borderRadius: isUser ? '20px 20px 4px 20px' : '20px 20px 20px 4px',
            position: 'relative',
          }}
        >
          <Typography variant="body1" sx={{ wordBreak: 'break-word' }}>
            {message.content}
          </Typography>

          {/* Bot message metadata */}
          {!isUser && message.intent && (
            <Box sx={{ mt: 1, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                size="small"
                label={message.intent}
                variant="outlined"
                sx={{ fontSize: '0.7rem', height: 20 }}
              />
              {message.confidence && (
                <Chip
                  size="small"
                  label={`${Math.round(message.confidence * 100)}%`}
                  color={message.confidence > 0.8 ? 'success' : message.confidence > 0.6 ? 'warning' : 'error'}
                  variant="outlined"
                  sx={{ fontSize: '0.7rem', height: 20 }}
                />
              )}
            </Box>
          )}

          {/* Message actions for bot messages */}
          {!isUser && (
            <Box
              sx={{
                position: 'absolute',
                top: -8,
                right: -8,
                display: 'flex',
                gap: 0.5,
                opacity: 0,
                transition: 'opacity 0.2s',
                '.message-bubble:hover &': {
                  opacity: 1,
                },
              }}
              className="message-actions"
            >
              <Tooltip title={t('messageActions.copy')}>
                <IconButton
                  size="small"
                  onClick={handleCopyMessage}
                  sx={{
                    backgroundColor: 'white',
                    boxShadow: 1,
                    '&:hover': { backgroundColor: 'grey.100' },
                  }}
                >
                  <CopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('messageActions.helpful')}>
                <IconButton
                  size="small"
                  onClick={() => handleFeedback(true)}
                  sx={{
                    backgroundColor: 'white',
                    boxShadow: 1,
                    '&:hover': { backgroundColor: 'success.light', color: 'white' },
                  }}
                >
                  <ThumbUpIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip title={t('messageActions.notHelpful')}>
                <IconButton
                  size="small"
                  onClick={() => handleFeedback(false)}
                  sx={{
                    backgroundColor: 'white',
                    boxShadow: 1,
                    '&:hover': { backgroundColor: 'error.light', color: 'white' },
                  }}
                >
                  <ThumbDownIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
          )}
        </Paper>

        {/* Timestamp */}
        <Typography
          variant="caption"
          color="textSecondary"
          sx={{
            display: 'block',
            textAlign: isUser ? 'right' : 'left',
            mt: 0.5,
            px: 1,
          }}
        >
          {formatTime(message.timestamp)}
        </Typography>
      </Box>

      {isUser && (
        <Avatar
          sx={{
            width: 32,
            height: 32,
            backgroundColor: 'secondary.main',
          }}
        >
          <PersonIcon fontSize="small" />
        </Avatar>
      )}
    </Box>
  );
};

export default MessageBubble;
