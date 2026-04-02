import { useState, useRef, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import MessageBubble from './components/MessageBubble';
import ChatInput from './components/ChatInput';
import Login from './components/Login';
import Signup from './components/Signup';
import { queryERPData, createChat, loadChatHistory, isAuthenticated, clearUserData, listChats, getUserId, updateChat, deleteChat } from './services/api';
import { Message, ERPResponse } from './types';
import './App.css';

function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'bot',
      content: 'Hello! I am your ERP Analytics Assistant. Ask me about purchase orders, invoices, attendance, or any other ERP data.',
      timestamp: new Date(),
    },
  ]);
  const [currentChatId, setCurrentChatId] = useState<number | null>(() => {
    const id = localStorage.getItem('current_chat_id');
    return id ? parseInt(id, 10) : null;
  });
  const [chatSessions, setChatSessions] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();

  const fetchSessions = async () => {
    const userId = getUserId();
    if (userId) {
      try {
        const sessions = await listChats(userId);
        setChatSessions(sessions);
      } catch (error) {
        console.error('Failed to fetch sessions:', error);
      }
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (currentChatId) {
      const fetchHistory = async () => {
        try {
          setIsLoading(true);
          const history = await loadChatHistory(currentChatId);
          if (history.messages && history.messages.length > 0) {
            const formattedMessages: Message[] = history.messages.map((m: any, idx: number) => ({
              id: `history-${idx}`,
              type: m.role === 'user' ? 'user' : 'bot',
              content: m.role === 'user' ? m.content : (m.summary || m.content),
              timestamp: m.created_at ? new Date(m.created_at) : new Date(),
              erpResponse: m.role === 'assistant' ? (m as ERPResponse) : undefined
            }));
            setMessages(formattedMessages);
          }
        } catch (error) {
          console.error('Failed to load history:', error);
        } finally {
          setIsLoading(false);
        }
      };
      fetchHistory();
    }
  }, [currentChatId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleLogout = () => {
    clearUserData();
    navigate('/login');
  };

  const handleRenameChat = async (e: React.MouseEvent, chatId: number, currentTitle: string) => {
    e.stopPropagation();
    const newTitle = prompt('Enter new chat title:', currentTitle);
    if (newTitle && newTitle !== currentTitle) {
      try {
        await updateChat(chatId, newTitle);
        await fetchSessions();
      } catch (error) {
        console.error('Failed to rename chat:', error);
        alert('Failed to rename chat. Please try again.');
      }
    }
  };

  const handleDeleteChat = async (e: React.MouseEvent, chatId: number) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this chat session?')) {
      try {
        await deleteChat(chatId);
        if (currentChatId === chatId) {
          clearChat();
        }
        await fetchSessions();
      } catch (error) {
        console.error('Failed to delete chat:', error);
        alert('Failed to delete chat. Please try again.');
      }
    }
  };

  const clearChat = () => {
    localStorage.removeItem('current_chat_id');
    setCurrentChatId(null);
    setMessages([
      {
        id: '1',
        type: 'bot',
        content: 'Hello! I am your ERP Analytics Assistant. Ask me about purchase orders, invoices, attendance, or any other ERP data.',
        timestamp: new Date(),
      },
    ]);
  };

  const handleNewChatClick = async () => {
    try {
      setIsLoading(true);
      const session = await createChat("New Chat");
      setCurrentChatId(session.chat_id);
      await fetchSessions(); // Refresh list to show new chat
      setMessages([
        {
          id: Date.now().toString(),
          type: 'bot',
          content: 'Hello! I am your ERP Analytics Assistant. Ask me about purchase orders, invoices, attendance, or any other ERP data.',
          timestamp: new Date(),
        },
      ]);
    } catch (error) {
      console.error('Failed to create new chat:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      let chatId = currentChatId;
      if (!chatId) {
        const session = await createChat(content.substring(0, 50));
        chatId = session.chat_id;
        setCurrentChatId(chatId);
        await fetchSessions(); // Refresh list to show new chat
      }

      const erpResponse = await queryERPData(content, chatId!);

      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: erpResponse.summary || 'Here is what I found:',
        timestamp: new Date(),
        erpResponse,
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (error: any) {
      console.error("Chat Error:", error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'bot',
        content: error.message || 'Sorry, I encountered an error while processing your request.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="sidebar-header">
          <button className="new-chat-btn" onClick={handleNewChatClick}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            New Chat
          </button>
        </div>
        <div className="sidebar-content">
          <div className="history-group">
            <h3>Chat History</h3>
            {chatSessions.map((session) => (
              <div
                key={session.id}
                className={`history-item ${currentChatId === session.id ? 'active' : ''}`}
                onClick={() => setCurrentChatId(session.id)}
              >
                <div className="history-item-content">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ marginRight: '8px', opacity: 0.7 }}>
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                  </svg>
                  <span className="truncate">{session.title}</span>
                </div>
                <div className="history-item-actions">
                  <button
                    className="action-btn edit"
                    onClick={(e) => handleRenameChat(e, session.id, session.title)}
                    title="Rename chat"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                  </button>
                  <button
                    className="action-btn delete"
                    onClick={(e) => handleDeleteChat(e, session.id)}
                    title="Delete chat"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="sidebar-footer">
          <button onClick={handleLogout} className="sidebar-action-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
              <polyline points="16 17 21 12 16 7"></polyline>
              <line x1="21" y1="12" x2="9" y2="12"></line>
            </svg>
            Logout
          </button>
        </div>
      </aside>

      <main className="main-content">
        <header className="chat-header">
          <div className="header-info">
            <h1 className="header-title">ERP Assistant</h1>
            <span className="model-badge">v2.0</span>
          </div>
        </header>

        <div className="messages-wrapper">
          <div className="messages-container">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isLoading && (
              <div className="typing-indicator-wrapper">
                <div className="typing-indicator">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        <div className="chat-input-wrapper">
          <div className="chat-input-container">
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
            <p className="input-disclaimer">ERP Assistant can make mistakes. Check important info.</p>
          </div>
        </div>
      </main>
    </div>
  );
}

function PrivateRoute({ children }: { children: React.ReactNode }) {
  return isAuthenticated() ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/"
          element={
            <PrivateRoute>
              <ChatInterface />
            </PrivateRoute>
          }
        />
      </Routes>
    </Router>
  );
}

export default App;
