import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { ScrollArea } from '../components/ui/scroll-area';
import { Send, Loader2, Activity, Trash2 } from 'lucide-react';

export default function ChatPage() {
  const { api, user } = useAuth();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [planUsage, setPlanUsage] = useState(null);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    api.get('/user/plan-usage').then(r => setPlanUsage(r.data)).catch(() => {});
  }, []);

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const text = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: text }]);
    setSending(true);

    try {
      const res = await api.post('/chat', { message: text, session_id: sessionId });
      setSessionId(res.data.session_id);
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    }
    setSending(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setSessionId(null);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] lg:h-[calc(100vh-4rem)]" data-testid="chat-page">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-[#6366F1]/20 flex items-center justify-center pulse-glow">
            <Activity className="w-5 h-5 text-[#6366F1]" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-white" style={{ fontFamily: 'Manrope' }}>Titan AI</h1>
            <p className="text-[11px] text-white/40">Your elite trading intelligence assistant</p>
          </div>
        </div>
        <Button variant="ghost" size="sm" className="text-white/30 hover:text-white/60 text-xs" onClick={clearChat} data-testid="clear-chat-btn">
          <Trash2 className="w-3.5 h-3.5 mr-1" /> Clear
        </Button>
      </div>

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto py-6 space-y-4 scroll-smooth">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-16 h-16 rounded-2xl bg-[#6366F1]/10 flex items-center justify-center mb-4 pulse-glow">
              <Activity className="w-8 h-8 text-[#6366F1]" />
            </div>
            <h2 className="text-lg font-bold text-white mb-2" style={{ fontFamily: 'Manrope' }}>Titan AI Trading Assistant</h2>
            <p className="text-sm text-white/40 max-w-md mb-6">
              Ask me about market analysis, trading strategies, technical indicators, or any trading question.
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full">
              {[
                'Analyze BTC price action for today',
                'What are the key support levels for NIFTY 50?',
                'Explain the RSI divergence strategy',
                'Best entry points for EUR/USD?',
              ].map((q, i) => (
                <button
                  key={i}
                  className="text-left px-4 py-3 rounded-lg bg-white/[0.03] border border-white/5 text-xs text-white/50 hover:bg-white/[0.06] hover:border-white/10 hover:text-white/70"
                  style={{ transition: 'background-color 0.2s, border-color 0.2s, color 0.2s' }}
                  onClick={() => { setInput(q); inputRef.current?.focus(); }}
                  data-testid={`suggestion-${i}`}
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in-up`}>
            <div className={`max-w-[80%] md:max-w-[70%] px-4 py-3 ${msg.role === 'user' ? 'chat-bubble-user' : 'chat-bubble-ai'}`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-2">
                  <Activity className="w-3 h-3 text-[#6366F1]" />
                  <span className="text-[10px] font-semibold text-[#6366F1] uppercase tracking-wider">Titan AI</span>
                </div>
              )}
              <p className="text-sm text-white/90 leading-relaxed whitespace-pre-wrap">{msg.content}</p>
            </div>
          </div>
        ))}

        {sending && (
          <div className="flex justify-start animate-fade-in-up">
            <div className="chat-bubble-ai px-4 py-3">
              <div className="flex items-center gap-2">
                <Loader2 className="w-3.5 h-3.5 text-[#6366F1] animate-spin" />
                <span className="text-xs text-white/40">Titan AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="pt-4 border-t border-white/10">
        <div className="flex items-center gap-3">
          <Input
            ref={inputRef}
            className="flex-1 bg-black/50 border-white/10 focus:border-[#6366F1] text-white text-sm"
            placeholder="Ask Titan AI about any market..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={sending}
            data-testid="chat-input"
          />
          <Button
            className="bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_15px_rgba(99,102,241,0.4)] active:scale-95 px-4"
            onClick={sendMessage}
            disabled={sending || !input.trim()}
            data-testid="chat-send-btn"
          >
            {sending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </Button>
        </div>
        <p className="text-[10px] text-white/20 mt-2 text-center">Titan AI may produce inaccurate information. Not financial advice. Always DYOR.</p>
      </div>
    </div>
  );
}
