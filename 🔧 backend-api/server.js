/**
 * Campus Assistant Backend API Server
 * Handles FAQ management, user authentication, and conversation logging
 */

const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const dotenv = require('dotenv');
const { Pool } = require('pg');
const redis = require('redis');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const winston = require('winston');
const fetch = require('node-fetch');

// Load environment variables
dotenv.config();

// Initialize Express app
const app = express();
const PORT = process.env.BACKEND_API_PORT || 3007;

// NLP engine base URL (configurable so it works both inside Docker and locally)
const NLP_API_URL = process.env.NLP_API_URL || 'http://localhost:8001';

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: './logs/backend-api.log' }),
    new winston.transports.Console()
  ]
});

// Database connection
// docker-compose provides discrete DB_* variables; we also accept a single
// DATABASE_URL. Prefer discrete vars when present so the container can reach
// the `postgres` service correctly.
const poolConfig = process.env.DATABASE_URL
  ? { connectionString: process.env.DATABASE_URL }
  : {
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT, 10) || 5432,
      database: process.env.DB_NAME || 'campus_assistant',
      user: process.env.DB_USER || 'postgres',
      password: process.env.DB_PASSWORD || 'postgres'
    };
poolConfig.ssl = process.env.NODE_ENV === 'production' && process.env.DB_SSL === 'true'
  ? { rejectUnauthorized: false }
  : false;

const pool = new Pool(poolConfig);

// Surface (but do not crash on) pool-level connection errors.
pool.on('error', (error) => {
  logger.warn('PostgreSQL pool error:', error.message);
});

// Redis connection
// Note: the connection is best-effort. The API remains functional (chat proxy,
// auth, FAQs) even when Redis is unavailable, so failures must never crash the
// process. We attach an 'error' handler and swallow connect rejections.
let redisClient;
let redisReady = false;
try {
  redisClient = redis.createClient({
    url: process.env.REDIS_URL || 'redis://localhost:6379'
  });

  redisClient.on('error', (error) => {
    if (redisReady) {
      logger.warn('Redis client error:', error.message);
    }
    redisReady = false;
  });

  redisClient.on('ready', () => {
    redisReady = true;
    logger.info('Redis connected successfully');
  });

  redisClient.connect().catch((error) => {
    logger.warn('Redis connection failed, continuing without cache:', error.message);
  });
} catch (error) {
  logger.warn('Redis initialization failed, continuing without cache:', error.message);
}

// Middleware
app.use(helmet());
app.use(cors({
  origin: function (origin, callback) {
    // Allow requests with no origin (like mobile apps or curl requests)
    if (!origin) return callback(null, true);
    
    // Allow all localhost and 127.0.0.1 origins for development
    if (origin.includes('localhost') || origin.includes('127.0.0.1')) {
      return callback(null, true);
    }
    
    // Allow specific origins
    const allowedOrigins = [
      'http://localhost:3008',
      'http://localhost:3009', 
      'http://127.0.0.1:3008',
      'http://127.0.0.1:36171'
    ];
    
    if (allowedOrigins.indexOf(origin) !== -1) {
      return callback(null, true);
    }
    
    return callback(new Error('Not allowed by CORS'));
  },
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  optionsSuccessStatus: 200
}));
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Authentication middleware
const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }

  jwt.verify(token, process.env.JWT_SECRET || 'campus_assistant_secret', (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid token' });
    }
    req.user = user;
    next();
  });
};

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    services: {
      database: pool ? 'connected' : 'disconnected',
      redis: redisReady ? 'connected' : 'disconnected'
    }
  });
});

// Chat proxy endpoint - Forward requests to NLP engine
app.post('/chat', async (req, res) => {
  try {
    const { message, session_id, language } = req.body;
    
    // Forward request to NLP engine
    const response = await fetch(`${NLP_API_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id,
        language
      })
    });
    
    const result = await response.json();
    
    // Log conversation for analytics
    try {
      await pool.query(
        `INSERT INTO conversations (session_id, user_message, bot_response, language, intent, confidence, platform, timestamp)
         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        [
          session_id,
          message,
          result.response,
          result.language || 'en',
          result.intent || 'general',
          result.confidence || 0.5,
          'web',
          new Date()
        ]
      );
    } catch (logError) {
      logger.warn('Failed to log conversation:', logError);
    }
    
    res.json(result);
    
  } catch (error) {
    logger.error('Chat proxy error:', error);
    res.status(500).json({
      response: 'I apologize, but I encountered an issue processing your request. Please try again.',
      error: 'Service temporarily unavailable'
    });
  }
});

// Authentication routes
app.post('/api/auth/register', async (req, res) => {
  try {
    const { username, email, password, role = 'student' } = req.body;

    // Validate input
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Username, email, and password are required' });
    }

    // Check if user exists
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE username = $1 OR email = $2',
      [username, email]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({ error: 'User already exists' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const result = await pool.query(
      'INSERT INTO users (username, email, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id, username, email, role',
      [username, email, hashedPassword, role]
    );

    const user = result.rows[0];

    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      process.env.JWT_SECRET || 'campus_assistant_secret',
      { expiresIn: '24h' }
    );

    res.status(201).json({
      message: 'User registered successfully',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      token
    });

  } catch (error) {
    logger.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({ error: 'Username and password are required' });
    }

    // Find user
    const result = await pool.query(
      'SELECT id, username, email, password_hash, role FROM users WHERE username = $1 OR email = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];

    // Verify password
    const validPassword = await bcrypt.compare(password, user.password_hash);
    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate JWT token
    const token = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      process.env.JWT_SECRET || 'campus_assistant_secret',
      { expiresIn: '24h' }
    );

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      token
    });

  } catch (error) {
    logger.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// FAQ management routes
app.get('/api/faqs', async (req, res) => {
  try {
    const { language = 'en', category, intent } = req.query;
    
    let query = 'SELECT * FROM faqs WHERE is_active = true';
    const params = [];
    
    if (category) {
      query += ' AND category_id = (SELECT id FROM faq_categories WHERE name = $' + (params.length + 1) + ')';
      params.push(category);
    }
    
    if (intent) {
      query += ' AND intent = $' + (params.length + 1);
      params.push(intent);
    }
    
    query += ' ORDER BY created_at DESC';
    
    const result = await pool.query(query, params);
    
    // Format FAQs for the requested language
    const faqs = result.rows.map(faq => ({
      id: faq.id,
      category_id: faq.category_id,
      question: faq[`question_${language}`] || faq.question_en,
      answer: faq[`answer_${language}`] || faq.answer_en,
      intent: faq.intent,
      keywords: faq.keywords,
      confidence_threshold: faq.confidence_threshold,
      created_at: faq.created_at
    }));
    
    res.json({ faqs, language });
    
  } catch (error) {
    logger.error('FAQ fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch FAQs' });
  }
});

app.post('/api/faqs', authenticateToken, async (req, res) => {
  try {
    const {
      category_id,
      question_en, answer_en,
      question_hi, answer_hi,
      question_bn, answer_bn,
      question_ta, answer_ta,
      question_mr, answer_mr,
      keywords,
      intent,
      confidence_threshold = 0.8
    } = req.body;

    if (!question_en || !answer_en || !intent) {
      return res.status(400).json({ error: 'English question, answer, and intent are required' });
    }

    const result = await pool.query(
      `INSERT INTO faqs (
        category_id, question_en, answer_en, question_hi, answer_hi,
        question_bn, answer_bn, question_ta, answer_ta, question_mr, answer_mr,
        keywords, intent, confidence_threshold
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
      RETURNING *`,
      [
        category_id, question_en, answer_en, question_hi, answer_hi,
        question_bn, answer_bn, question_ta, answer_ta, question_mr, answer_mr,
        keywords, intent, confidence_threshold
      ]
    );

    res.status(201).json({
      message: 'FAQ created successfully',
      faq: result.rows[0]
    });

  } catch (error) {
    logger.error('FAQ creation error:', error);
    res.status(500).json({ error: 'Failed to create FAQ' });
  }
});

// Chat conversation logging
app.post('/api/conversations', async (req, res) => {
  try {
    const {
      session_id,
      user_id,
      message_type,
      content,
      language,
      intent,
      confidence,
      response_time_ms,
      escalated_to_human = false
    } = req.body;

    // Get or create session
    let sessionResult = await pool.query(
      'SELECT id FROM conversation_sessions WHERE session_token = $1',
      [session_id]
    );

    let sessionDbId;
    if (sessionResult.rows.length === 0) {
      // Create new session
      const newSession = await pool.query(
        'INSERT INTO conversation_sessions (user_id, session_token, language) VALUES ($1, $2, $3) RETURNING id',
        [user_id, session_id, language]
      );
      sessionDbId = newSession.rows[0].id;
    } else {
      sessionDbId = sessionResult.rows[0].id;
    }

    // Log message
    const result = await pool.query(
      `INSERT INTO conversation_messages (
        session_id, message_type, content, language, intent, confidence,
        response_time_ms, escalated_to_human
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING *`,
      [sessionDbId, message_type, content, language, intent, confidence, response_time_ms, escalated_to_human]
    );

    res.status(201).json({
      message: 'Conversation logged successfully',
      conversation_message: result.rows[0]
    });

  } catch (error) {
    logger.error('Conversation logging error:', error);
    res.status(500).json({ error: 'Failed to log conversation' });
  }
});

// Analytics endpoints
app.get('/api/analytics/daily-metrics', authenticateToken, async (req, res) => {
  try {
    const { date = new Date().toISOString().split('T')[0] } = req.query;
    
    const result = await pool.query(
      'SELECT * FROM daily_metrics WHERE date = $1',
      [date]
    );
    
    if (result.rows.length === 0) {
      // Calculate metrics for the date
      const metrics = await calculateDailyMetrics(date);
      res.json(metrics);
    } else {
      res.json(result.rows[0]);
    }
    
  } catch (error) {
    logger.error('Analytics fetch error:', error);
    res.status(500).json({ error: 'Failed to fetch analytics' });
  }
});

// Helper function to calculate daily metrics
async function calculateDailyMetrics(date) {
  try {
    const startDate = new Date(date);
    const endDate = new Date(date);
    endDate.setDate(endDate.getDate() + 1);

    // Total conversations
    const conversationsResult = await pool.query(
      'SELECT COUNT(*) as total FROM conversation_sessions WHERE started_at >= $1 AND started_at < $2',
      [startDate, endDate]
    );

    // Total messages
    const messagesResult = await pool.query(
      'SELECT COUNT(*) as total FROM conversation_messages WHERE created_at >= $1 AND created_at < $2',
      [startDate, endDate]
    );

    // Language distribution
    const languageResult = await pool.query(
      `SELECT language, COUNT(*) as count 
       FROM conversation_sessions 
       WHERE started_at >= $1 AND started_at < $2 
       GROUP BY language`,
      [startDate, endDate]
    );

    // Intent distribution
    const intentResult = await pool.query(
      `SELECT intent, COUNT(*) as count 
       FROM conversation_messages 
       WHERE created_at >= $1 AND created_at < $2 AND intent IS NOT NULL
       GROUP BY intent`,
      [startDate, endDate]
    );

    // Average response time
    const responseTimeResult = await pool.query(
      `SELECT AVG(response_time_ms) as avg_time 
       FROM conversation_messages 
       WHERE created_at >= $1 AND created_at < $2 AND response_time_ms IS NOT NULL`,
      [startDate, endDate]
    );

    // Escalation rate
    const escalationResult = await pool.query(
      `SELECT 
         COUNT(*) as total_messages,
         COUNT(*) FILTER (WHERE escalated_to_human = true) as escalated_messages
       FROM conversation_messages 
       WHERE created_at >= $1 AND created_at < $2`,
      [startDate, endDate]
    );

    const metrics = {
      date,
      total_conversations: parseInt(conversationsResult.rows[0].total),
      total_messages: parseInt(messagesResult.rows[0].total),
      language_distribution: languageResult.rows.reduce((acc, row) => {
        acc[row.language] = parseInt(row.count);
        return acc;
      }, {}),
      intent_distribution: intentResult.rows.reduce((acc, row) => {
        acc[row.intent] = parseInt(row.count);
        return acc;
      }, {}),
      avg_response_time_ms: parseFloat(responseTimeResult.rows[0].avg_time) || 0,
      escalation_rate: escalationResult.rows[0].total_messages > 0 
        ? escalationResult.rows[0].escalated_messages / escalationResult.rows[0].total_messages 
        : 0
    };

    // Store calculated metrics
    await pool.query(
      `INSERT INTO daily_metrics (
        date, total_conversations, total_messages, language_distribution,
        intent_distribution, avg_response_time_ms, escalation_rate
      ) VALUES ($1, $2, $3, $4, $5, $6, $7)
      ON CONFLICT (date) DO UPDATE SET
        total_conversations = EXCLUDED.total_conversations,
        total_messages = EXCLUDED.total_messages,
        language_distribution = EXCLUDED.language_distribution,
        intent_distribution = EXCLUDED.intent_distribution,
        avg_response_time_ms = EXCLUDED.avg_response_time_ms,
        escalation_rate = EXCLUDED.escalation_rate`,
      [
        date,
        metrics.total_conversations,
        metrics.total_messages,
        JSON.stringify(metrics.language_distribution),
        JSON.stringify(metrics.intent_distribution),
        metrics.avg_response_time_ms,
        metrics.escalation_rate
      ]
    );

    return metrics;

  } catch (error) {
    logger.error('Metrics calculation error:', error);
    throw error;
  }
}

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', error);
  res.status(500).json({ error: 'Internal server error' });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Endpoint not found' });
});

// Start server
app.listen(PORT, () => {
  logger.info(`Campus Assistant Backend API running on port ${PORT}`);
  logger.info(`Health check: http://localhost:${PORT}/health`);
});

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully');
  
  if (redisClient) {
    await redisClient.quit();
  }
  
  await pool.end();
  process.exit(0);
});

module.exports = app;
