import { useState } from 'react';
import { Send, Mic, Sparkles } from 'lucide-react';
import ActionCard from './ActionCard';

export default function Assistant() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant'; content: string }>>([]);

  const handleSend = () => {
    if (message.trim()) {
      setMessages([...messages, { role: 'user', content: message }]);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-full relative">
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
            {/* Radial Glow */}
            <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />
            
            {/* Hero Icon */}
            <div className="relative z-10 mb-8 animate-pulse-glow">
              <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-[0_0_40px_rgba(99,102,241,0.5)]">
                <Sparkles className="w-12 h-12 text-white" />
              </div>
            </div>

            {/* Heading */}
            <h2 className="text-3xl font-bold text-white mb-3 relative z-10">What would you like to do?</h2>
            <p className="text-gray-400 mb-12 relative z-10">Ask me anything or choose from the options below</p>

            {/* Quick Action Cards */}
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
                  className={`max-w-[70%] px-5 py-3 rounded-2xl ${
                    msg.role === 'user'
                      ? 'bg-blue-600 text-white'
                      : 'bg-white/5 backdrop-blur-sm border border-white/10 text-gray-200'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="px-8 py-6 border-t border-white/5 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto">
          <div className="relative flex items-center gap-3 bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl px-5 py-3 focus-within:border-blue-500/50 focus-within:shadow-[0_0_30px_rgba(59,130,246,0.15)] transition-all duration-200">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Tell me what you want to do..."
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
              disabled={!message.trim()}
              className="p-2 rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-40 disabled:cursor-not-allowed hover:shadow-[0_0_20px_rgba(59,130,246,0.4)] transition-all duration-200"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
