import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './Chatbot.css';

const API_URL = 'http://localhost:8000/api/chat';

function Chatbot() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Hi! I\'m here to help you find community college courses that satisfy your Cal Poly GE requirements. What would you like to know?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([
    'What is Cal-GETC?',
    'I need courses for Area 3 (Arts & Humanities)',
    'Explain IGETC',
    'Show me all available courses'
  ]);
  const [language, setLanguage] = useState('en');
  const [showAbout, setShowAbout] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const [enrollableCourses, setEnrollableCourses] = useState(new Set());
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (messageText) => {
    if (!messageText && !input.trim()) return;

    const userMessage = messageText || input.trim();
    const newMessages = [...messages, { role: 'user', content: userMessage }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);
    setSuggestions([]);

    try {
      const response = await axios.post(API_URL, {
        messages: newMessages,
        context: { language: language }
      });

      const { response: botResponse, suggestions: newSuggestions, courses, sources, enrollable_course_codes } = response.data;

      // Add assistant message
      setMessages([...newMessages, {
        role: 'assistant',
        content: botResponse,
        courses: courses,
        sources: sources
      }]);

      // Update enrollable courses if user expressed interest
      if (enrollable_course_codes && enrollable_course_codes.length > 0) {
        setEnrollableCourses(prev => new Set([...prev, ...enrollable_course_codes]));
      }

      // Update suggestions if provided
      if (newSuggestions && newSuggestions.length > 0) {
        setSuggestions(newSuggestions);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      setMessages([...newMessages, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please make sure the backend server is running on port 8000.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  const clearConversation = () => {
    if (window.confirm('Are you sure you want to clear the conversation?')) {
      setMessages([
        {
          role: 'assistant',
          content: 'Hi! I\'m here to help you find community college courses that satisfy your Cal Poly GE requirements. What would you like to know?'
        }
      ]);
      setSuggestions([
        'What is Cal-GETC?',
        'I need courses for Area 3 (Arts & Humanities)',
        'Explain IGETC',
        'Show me all available courses'
      ]);
    }
  };

  const downloadTranscript = () => {
    const transcript = messages.map(msg => {
      const timestamp = new Date().toLocaleString();
      return `[${msg.role.toUpperCase()}] ${timestamp}\n${msg.content}\n\n`;
    }).join('---\n\n');

    const blob = new Blob([transcript], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cvc-chat-transcript-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const toggleAbout = () => {
    setShowAbout(!showAbout);
  };

  const toggleSources = () => {
    setShowSources(!showSources);
  };

  const copyMessage = (content) => {
    navigator.clipboard.writeText(content);
    // Could add a toast notification here
    alert('Message copied to clipboard!');
  };

  const handleEnroll = (course) => {
    alert(`Enroll in ${course.course_code} - ${course.title}\n\nCollege: ${course.college}\n\nThis is a mock enrollment button. In production, this would redirect to the college's enrollment page.`);
  };

  return (
    <div className="chatbot-container">
      {/* Header */}
      <div className="chatbot-header">
        <div className="header-content">
          <div className="header-title">
            <h1>🎓 California Virtual Campus</h1>
            <p>GE Course Finder for Cal Poly Students</p>
          </div>
          <div className="header-actions">
            {/* Language Selector */}
            <select
              className="language-select"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              title="Select Language / Seleccionar idioma / 选择语言"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="zh">中文</option>
            </select>

            {/* Clear Conversation */}
            <button
              className="header-button"
              onClick={clearConversation}
              title="Clear Conversation"
            >
              🗑️
            </button>

            {/* Download Transcript */}
            <button
              className="header-button"
              onClick={downloadTranscript}
              title="Download Transcript"
            >
              📥
            </button>

            {/* Sources */}
            <button
              className="header-button"
              onClick={toggleSources}
              title="View Sources"
            >
              📚
            </button>

            {/* About */}
            <button
              className="header-button"
              onClick={toggleAbout}
              title="About"
            >
              ℹ️
            </button>
          </div>
        </div>
      </div>

      {/* About Modal */}
      {showAbout && (
        <div className="modal-overlay" onClick={toggleAbout}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>About CVC Chatbot</h2>
              <button className="modal-close" onClick={toggleAbout}>×</button>
            </div>
            <div className="modal-body">
              <p><strong>California Virtual Campus (CVC) GE Course Finder</strong></p>
              <p>This chatbot helps California community college students find courses that satisfy General Education (GE) requirements for transfer to Cal Poly and other universities.</p>

              <h3>Features:</h3>
              <ul>
                <li>🔍 Semantic search across 1,981 courses</li>
                <li>🎓 GE system explanations (IGETC, Cal-GETC, Cal-Breadth)</li>
                <li>🏫 Courses from multiple community colleges</li>
                <li>📋 Transfer agreement information</li>
                <li>🤖 AI-powered responses using Claude Haiku</li>
              </ul>

              <h3>GE Systems:</h3>
              <p><strong>IGETC:</strong> Intersegmental General Education Transfer Curriculum (pre-Fall 2025)</p>
              <p><strong>Cal-GETC:</strong> California General Education Transfer Curriculum (Fall 2025+)</p>
              <p><strong>Cal-Breadth:</strong> UC campus-specific breadth requirements</p>

              <h3>Data Sources:</h3>
              <ul>
                <li>Course catalogs from CA community colleges</li>
                <li>Transfer agreements via ASSIST.org</li>
                <li>GE requirement documentation</li>
              </ul>

              <p className="modal-footer-text">
                <strong>Powered by:</strong> AWS Bedrock (Claude Haiku 4.5 + Titan Embeddings) • OpenSearch • React
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Sources Panel */}
      {showSources && (
        <div className="sources-panel">
          <div className="sources-header">
            <h3>📚 Sources</h3>
            <button className="sources-close" onClick={toggleSources}>×</button>
          </div>
          <div className="sources-content">
            {messages.filter(msg => msg.sources).length > 0 ? (
              messages.filter(msg => msg.sources).map((msg, idx) => (
                <div key={idx} className="source-group">
                  <h4>Response {idx + 1}:</h4>
                  {msg.sources && msg.sources.map((source, sIdx) => (
                    <div key={sIdx} className="source-item">
                      <div className="source-score">
                        Relevance: {(source.score * 100).toFixed(1)}%
                      </div>
                      <div className="source-text">{source.text.substring(0, 150)}...</div>
                      {source.metadata && (
                        <div className="source-meta">
                          {source.metadata.college && <span>📍 {source.metadata.college}</span>}
                          {source.metadata.course_code && <span>📖 {source.metadata.course_code}</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))
            ) : (
              <p className="no-sources">No sources yet. Start chatting to see sources!</p>
            )}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="chatbot-messages">
        {messages.map((message, index) => (
          <div key={index} className={`message-wrapper ${message.role}`}>
            <div className="message-avatar">
              {message.role === 'user' ? '👤' : '🎓'}
            </div>
            <div className="message-container">
              <div className="message-header">
                <span className="message-role">
                  {message.role === 'user' ? 'You' : 'CVC Assistant'}
                </span>
                <button
                  className="copy-button"
                  onClick={() => copyMessage(message.content)}
                  title="Copy message"
                >
                  📋
                </button>
              </div>
              <div className="message-content">
                <div
                  className="message-text"
                  dangerouslySetInnerHTML={{
                    __html: message.content
                      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                      .replace(/\*(.*?)\*/g, '<em>$1</em>')
                      .replace(/\n/g, '<br />')
                  }}
                />

                {/* Display courses if present */}
                {message.courses && message.courses.length > 0 && (
                  <div className="courses-list">
                    {message.courses.map((course, idx) => (
                      <div key={idx} className="course-card">
                        <div className="course-header">
                          <div>
                            <strong>{course.course_code}</strong> - {course.title}
                          </div>
                        </div>
                        <div className="course-details">
                          <div className="course-college">📍 {course.college}</div>
                          <div className="course-units">⏱️ {course.units} units</div>
                        </div>
                        <div className="course-description">{course.description}</div>
                        <div className="course-footer">
                          <div className="course-ge">
                            {course.ge_areas.map((ge, geIdx) => (
                              <span key={geIdx} className="ge-badge">{ge}</span>
                            ))}
                          </div>
                          {enrollableCourses.has(course.course_code) && (
                            <button
                              className="enroll-button"
                              onClick={() => handleEnroll(course)}
                            >
                              📝 Enroll
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && !isLoading && (
        <div className="suggestions">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              className="suggestion-button"
              onClick={() => handleSuggestionClick(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <form className="chatbot-input" onSubmit={handleSubmit}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          placeholder="Ask about GE requirements, courses, or transfer info..."
          disabled={isLoading}
          autoFocus
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          {isLoading ? '...' : 'Send'}
        </button>
      </form>
    </div>
  );
}

export default Chatbot;
