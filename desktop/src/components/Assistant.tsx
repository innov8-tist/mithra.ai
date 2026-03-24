import { useState, useRef, useEffect } from 'react';
import { Send, Mic, Sparkles, Globe, Search } from 'lucide-react';
import ActionCard from './ActionCard';
import MessageContent from './MessageContent';
import TypingIndicator from './TypingIndicator';

type ChatMode = 'autofill' | 'advisor';

const API_BASE_URL = 'http://localhost:8000';

export default function Assistant() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);
  const [chatMode, setChatMode] = useState<ChatMode>('advisor');
  const [showModeSelector, setShowModeSelector] = useState(false);
  const [popupPos, setPopupPos] = useState({ bottom: 0, left: 0 });
  const [isLoading, setIsLoading] = useState(false);
  const popupRef = useRef<HTMLDivElement>(null);
  const modeButtonRef = useRef<HTMLButtonElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Recalculate position every time popup opens
  useEffect(() => {
    if (showModeSelector && modeButtonRef.current) {
      const rect = modeButtonRef.current.getBoundingClientRect();
      setPopupPos({
        bottom: window.innerHeight - rect.top + 12,
        left: rect.left,
      });
    }
  }, [showModeSelector]);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (
        popupRef.current && !popupRef.current.contains(e.target as Node) &&
        modeButtonRef.current && !modeButtonRef.current.contains(e.target as Node)
      ) {
        setShowModeSelector(false);
      }
    };
    if (showModeSelector) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [showModeSelector]);

  const handleSend = async () => {
    if (!message.trim()) return;
    
    const userMessage = message;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setMessage('');

    if (chatMode === 'advisor') {
      setIsLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/query`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ query: userMessage }),
        });

        if (response.ok) {
          const data = await response.json();
          
          // Parse the response - it's a string in data.result
          const responseText = data.result || data.response || data.answer || 'No response received';
          
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            content: responseText
          }]);
        } else {
          setMessages(prev => [...prev, { 
            role: 'assistant', 
            content: 'Sorry, I encountered an error. Please try again.'
          }]);
        }
      } catch (error) {
        console.error('Query failed:', error);
        setMessages(prev => [...prev, { 
          role: 'assistant', 
          content: 'Failed to connect to the server. Please ensure the backend is running.'
        }]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // AutoFill mode - placeholder
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'AutoFill mode will control the browser to fill forms automatically.'
      }]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full">

      {/* Mode Selector Popup — fixed to viewport, always above input bar */}
      {showModeSelector && (
        <div
          ref={popupRef}
          style={{
            position: 'fixed',
            bottom: popupPos.bottom,
            left: popupPos.left,
            zIndex: 9999,
          }}
          className="w-80 bg-[#12122a] border border-white/20 rounded-xl p-3 shadow-2xl animate-fadeInUp"
        >
          <div className="text-xs text-gray-400 mb-3 px-2">Switch mode</div>

          <button
            onClick={() => { setChatMode('autofill'); setShowModeSelector(false); }}
            className={`w-full flex items-start gap-3 px-3 py-3 rounded-lg mb-1 transition-all duration-200 ${
              chatMode === 'autofill'
                ? 'bg-blue-500/20 border border-blue-500/30'
                : 'hover:bg-white/5'
            }`}
          >
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0">
              <Globe className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-left">
              <div className="text-sm font-semibold text-white">AutoFill</div>
              <div className="text-xs text-gray-400">Browse websites & fill forms for you</div>
            </div>
            {chatMode === 'autofill' && (
              <div className="ml-auto"><div className="w-2 h-2 rounded-full bg-blue-500 mt-1" /></div>
            )}
          </button>

          <button
            onClick={() => { setChatMode('advisor'); setShowModeSelector(false); }}
            className={`w-full flex items-start gap-3 px-3 py-3 rounded-lg transition-all duration-200 ${
              chatMode === 'advisor'
                ? 'bg-blue-500/20 border border-blue-500/30'
                : 'hover:bg-white/5'
            }`}
          >
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0">
              <Search className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-left">
              <div className="text-sm font-semibold text-white">Advisor</div>
              <div className="text-xs text-gray-400">Search schemes & answer questions</div>
            </div>
            {chatMode === 'advisor' && (
              <div className="ml-auto"><div className="w-2 h-2 rounded-full bg-blue-500 mt-1" /></div>
            )}
          </button>
        </div>
      )}

      {/* Status Bar */}
      <div className="px-8 py-4 border-b border-white/5 backdrop-blur-sm">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-gray-400">Ready to help</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto px-8 py-8">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full animate-fadeInUp">
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />

            <div className="relative z-10 mb-8">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(99,102,241,0.5)]">
                <Sparkles className="w-12 h-12 text-white" />
              </div>
            </div>

            <h2 className="text-3xl font-bold text-white mb-3 relative z-10">What would you like to do?</h2>
            <p className="text-gray-400 mb-12 relative z-10">Ask me anything or choose from the options below</p>

            <div className="grid grid-cols-2 gap-4 max-w-2xl w-full relative z-10">
              <ActionCard
                icon="🌍"
                title="Apply for Passport"
                description="Start your passport application"
                onClick={() => setMessage('I want to apply for a passport')}
              />
              <ActionCard
                icon="🔒"
                title="Reset Password"
                description="Change your account password"
                onClick={() => setMessage('I need to reset my password')}
              />
              <ActionCard
                icon="✨"
                title="Check Schemes"
                description="View available government schemes"
                onClick={() => setMessage('Show me available schemes')}
              />
              <ActionCard
                icon="📄"
                title="Ask about Documents"
                description="Get help with your documents"
                onClick={() => setMessage('I have questions about documents')}
              />
            </div>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto space-y-4">
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeInUp`}
              >
                <div
                  className={`max-w-[70%] px-5 py-3 rounded-2xl whitespace-pre-wrap ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/5 backdrop-blur-sm border border-white/10 text-gray-200'
                  }`}
                >
                  <MessageContent content={msg.content} />
                </div>
              </div>
            ))}
            {/* Typing Indicator */}
            {isLoading && <TypingIndicator />}
            {/* Scroll anchor */}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-8 py-6 border-t border-white/5 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl px-5 py-3 focus-within:border-blue-500/50 focus-within:shadow-[0_0_30px_rgba(59,130,246,0.15)] transition-all duration-200">
            
            <button
              ref={modeButtonRef}
              onClick={() => setShowModeSelector(!showModeSelector)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition-all duration-200 flex-shrink-0"
            >
              {chatMode === 'autofill' ? (
                <Globe className="w-4 h-4 text-blue-400" />
              ) : (
                <Search className="w-4 h-4 text-blue-400" />
              )}
              <span className="text-xs text-gray-400 capitalize">{chatMode} mode</span>
            </button>

            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder={
                chatMode === 'autofill'
                  ? 'Tell me which form to fill...'
                  : 'Ask me anything about schemes...'
              }
              className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-sm"
            />

            <button
              onClick={() => console.log('Voice input')}
              className="p-2 rounded-lg text-gray-400 hover:text-blue-400 hover:bg-white/5 transition-all duration-200"
            >
              <Mic className="w-5 h-5" />
            </button>

            <button
              onClick={handleSend}
              disabled={!message.trim() || isLoading}
              className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-200"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Send className="w-5 h-5" />
              )}
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}