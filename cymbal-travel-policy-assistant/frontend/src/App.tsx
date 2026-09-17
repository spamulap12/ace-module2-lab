import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  TextField,
  IconButton,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  CircularProgress,
  Avatar,
  Divider,
  Button,
  Tooltip,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import VerifiedUserIcon from '@mui/icons-material/VerifiedUser';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import MenuBookIcon from '@mui/icons-material/MenuBook';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';

interface ContextChunk {
  chunk_id: string;
  section: string;
  title: string;
  content: string;
}

interface Message {
  id: string;
  sender: 'user' | 'agent';
  text: string;
  context?: ContextChunk[];
  timestamp: string;
}

const API_BASE_URL = 'http://localhost:8000';

const PRESET_SCENARIOS = [
  {
    label: '🇨🇭 Switzerland Meal Cap',
    query: 'What is the meal cap for Switzerland?',
    code: 'Scenario A'
  },
  {
    label: '✈️ First Class: Dublin -> Zurich',
    query: 'Can I book a first-class flight from Dublin to Zurich?',
    code: 'Scenario B'
  },
  {
    label: '📺 Hotel TV Movies',
    query: 'Can I buy a movie on the hotel TV?',
    code: 'Scenario C'
  },
  {
    label: '🐕 Bringing Pets on Travel',
    query: 'Can I bring my pet dog on a business trip?',
    code: 'Scenario D'
  }
];

export default function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      sender: 'agent',
      text: 'Hello! I am the **Cymbal Group Travel Policy Concierge**. I am here to help Cymbal Group\'s 200,000 global employees navigate our corporate travel and expense policies.\n\nHow may I assist you today?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(2, 9));
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const handleSendMessage = async (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputQuery('');
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: query,
          session_id: sessionId,
        }),
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      const data = await response.json();

      const agentMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        text: data.response,
        context: data.retrieved_context,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, agentMsg]);
    } catch (error) {
      console.error('Chat API Error:', error);
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: 'agent',
        text: "I'm sorry, I encountered an issue connecting to the Cymbal Travel Policy service. Please ensure the backend is running at http://localhost:8000.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearHistory = async () => {
    try {
      await fetch(`${API_BASE_URL}/clear_session?session_id=${sessionId}`, {
        method: 'POST',
      });
    } catch (e) {
      console.error('Error clearing session:', e);
    }
    setMessages([
      {
        id: Date.now().toString(),
        sender: 'agent',
        text: 'Session history cleared. How else can I help you with Cymbal Group travel policies?',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', bgcolor: '#F8FAFC' }}>
      {/* Top Header Bar */}
      <Box className="glass-header" sx={{ py: 2, px: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: '#2563EB', width: 44, height: 44, boxShadow: '0 0 12px rgba(37,99,235,0.4)' }}>
            <FlightTakeoffIcon />
          </Avatar>
          <Box>
            <Typography variant="h6" sx={{ fontWeight: 700, lineHeight: 1.2, color: '#FFFFFF' }}>
              Cymbal Group Travel Policy Concierge
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <Chip
                icon={<VerifiedUserIcon style={{ color: '#10B981', fontSize: 14 }} />}
                label="Grounded Policy AI (Gemini 3.6 Flash)"
                size="small"
                sx={{ height: 20, fontSize: '0.7rem', bgcolor: 'rgba(255,255,255,0.12)', color: '#E2E8F0' }}
              />
              <Typography variant="caption" sx={{ color: '#94A3B8' }}>
                • 200k Employees Global
              </Typography>
            </Box>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Tooltip title="Clear chat session memory">
            <Button
              variant="outlined"
              size="small"
              startIcon={<DeleteSweepIcon />}
              onClick={handleClearHistory}
              sx={{ color: '#94A3B8', borderColor: 'rgba(255,255,255,0.2)', '&:hover': { borderColor: '#FFFFFF', color: '#FFFFFF' } }}
            >
              Clear Chat
            </Button>
          </Tooltip>
        </Box>
      </Box>

      {/* Main Content Area */}
      <Container maxWidth="lg" sx={{ flex: 1, display: 'flex', flexDirection: 'column', py: 3, overflow: 'hidden' }}>
        <Paper
          elevation={1}
          sx={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            overflow: 'hidden',
            borderRadius: 4,
            border: '1px solid #E2E8F0',
          }}
        >
          {/* Preset Test Scenarios Banner */}
          <Box sx={{ p: 2, bgcolor: '#F1F5F9', borderBottom: '1px solid #E2E8F0' }}>
            <Typography variant="caption" sx={{ fontWeight: 600, color: '#475569', textTransform: 'uppercase', letterSpacing: 0.5, mb: 1, display: 'block' }}>
              ⚡ Quick Test Scenarios
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {PRESET_SCENARIOS.map((scenario) => (
                <Chip
                  key={scenario.code}
                  label={scenario.label}
                  onClick={() => handleSendMessage(scenario.query)}
                  clickable
                  color="primary"
                  variant="outlined"
                  size="small"
                  sx={{
                    bgcolor: '#FFFFFF',
                    borderColor: '#CBD5E1',
                    '&:hover': { bgcolor: '#E0F2FE', borderColor: '#2563EB' },
                  }}
                />
              ))}
            </Box>
          </Box>

          {/* Messages Feed */}
          <Box sx={{ flex: 1, p: 3, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 2 }}>
            {messages.map((msg) => (
              <Box
                key={msg.id}
                sx={{
                  display: 'flex',
                  justifyContent: msg.sender === 'user' ? 'flex-end' : 'flex-start',
                  gap: 1.5,
                }}
              >
                {msg.sender === 'agent' && (
                  <Avatar sx={{ bgcolor: '#1E3A8A', width: 36, height: 36, mt: 0.5 }}>
                    <SmartToyIcon fontSize="small" />
                  </Avatar>
                )}

                <Box sx={{ maxWidth: '80%' }}>
                  <Paper
                    className={msg.sender === 'user' ? 'message-bubble-user' : 'message-bubble-agent'}
                    sx={{ p: 2.5 }}
                  >
                    <Typography
                      variant="body1"
                      sx={{
                        whiteSpace: 'pre-line',
                        lineHeight: 1.6,
                        fontSize: '0.95rem',
                      }}
                    >
                      {msg.text}
                    </Typography>

                    {/* Retrieved Context Citations for Agent Replies */}
                    {msg.sender === 'agent' && msg.context && msg.context.length > 0 && (
                      <Box sx={{ mt: 2, pt: 1.5, borderTop: '1px solid #E2E8F0' }}>
                        <Accordion elevation={0} sx={{ bgcolor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px !important' }}>
                          <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <MenuBookIcon fontSize="small" color="primary" />
                              <Typography variant="caption" sx={{ fontWeight: 600, color: '#1E3A8A' }}>
                                Retrieved Policy Context ({msg.context.length} sections cited)
                              </Typography>
                            </Box>
                          </AccordionSummary>
                          <AccordionDetails sx={{ pt: 0 }}>
                            {msg.context.map((chunk, idx) => (
                              <Box key={idx} sx={{ mb: 1.5, '&:last-child': { mb: 0 } }}>
                                <Typography variant="caption" sx={{ fontWeight: 700, color: '#0F172A', display: 'block' }}>
                                  📌 {chunk.title}
                                </Typography>
                                <Typography variant="caption" sx={{ color: '#475569', display: 'block', mt: 0.5, bgcolor: '#FFFFFF', p: 1, borderRadius: 1, border: '1px solid #F1F5F9' }}>
                                  {chunk.content}
                                </Typography>
                              </Box>
                            ))}
                          </AccordionDetails>
                        </Accordion>
                      </Box>
                    )}
                  </Paper>

                  <Typography
                    variant="caption"
                    sx={{
                      display: 'block',
                      mt: 0.5,
                      px: 1,
                      textAlign: msg.sender === 'user' ? 'right' : 'left',
                      color: '#94A3B8',
                      fontSize: '0.75rem',
                    }}
                  >
                    {msg.timestamp}
                  </Typography>
                </Box>

                {msg.sender === 'user' && (
                  <Avatar sx={{ bgcolor: '#2563EB', width: 36, height: 36, mt: 0.5 }}>
                    <PersonIcon fontSize="small" />
                  </Avatar>
                )}
              </Box>
            ))}

            {loading && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, p: 2 }}>
                <Avatar sx={{ bgcolor: '#1E3A8A', width: 36, height: 36 }}>
                  <SmartToyIcon fontSize="small" />
                </Avatar>
                <Paper sx={{ p: 2, bgcolor: '#FFFFFF', borderRadius: '18px 18px 18px 2px', border: '1px solid #E2E8F0', display: 'flex', alignItems: 'center', gap: 1.5 }}>
                  <CircularProgress size={18} color="primary" />
                  <Typography variant="body2" sx={{ color: '#475569', fontStyle: 'italic' }}>
                    Retrieving policy context & analyzing rules...
                  </Typography>
                </Paper>
              </Box>
            )}

            <div ref={messagesEndRef} />
          </Box>

          <Divider />

          {/* Input Area */}
          <Box sx={{ p: 2, bgcolor: '#FFFFFF', display: 'flex', alignItems: 'center', gap: 1.5 }}>
            <TextField
              fullWidth
              variant="outlined"
              placeholder="Ask any question about Cymbal Group travel & expense policy..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              disabled={loading}
              size="medium"
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 3,
                  bgcolor: '#F8FAFC',
                },
              }}
            />
            <IconButton
              color="primary"
              onClick={() => handleSendMessage()}
              disabled={!inputQuery.trim() || loading}
              sx={{
                bgcolor: '#1E3A8A',
                color: '#FFFFFF',
                p: 1.5,
                '&:hover': { bgcolor: '#2563EB' },
                '&.Mui-disabled': { bgcolor: '#E2E8F0', color: '#94A3B8' },
              }}
            >
              <SendIcon />
            </IconButton>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
}
