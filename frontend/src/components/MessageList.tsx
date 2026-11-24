import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types/chat';
import { MessageItem } from './MessageItem';
import { Bot, Sparkles, Loader2, ArrowRight, ShieldCheck, Zap, Database } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessage[];
  loading: boolean;
  onSelectPrompt?: (prompt: string) => void;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  loading,
  onSelectPrompt,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const suggestions = [
    {
      title: 'Explain Quantum Computing',
      desc: 'Simple analogy for qubits & superposition',
      prompt: 'Explain quantum computing simply in 2 paragraphs.',
      icon: <Sparkles className="w-4 h-4 text-purple-500" />,
    },
    {
      title: 'Test Response Caching',
      desc: 'Demonstrate sub-30ms cache hit',
      prompt: 'What is the boiling point of water? Reply in one sentence.',
      icon: <Database className="w-4 h-4 text-emerald-500" />,
    },
    {
      title: 'Key Failover Simulation',
      desc: 'Automatic switch when key_1 hits 429',
      prompt: 'Explain how API key failover prevents downtime in LLM gateways.',
      icon: <Zap className="w-4 h-4 text-amber-500" />,
    },
    {
      title: 'Multi-Turn Persona Test',
      desc: 'Evaluate session context retention',
      prompt: 'My favorite color is emerald green. Remember this for our conversation.',
      icon: <ShieldCheck className="w-4 h-4 text-indigo-500" />,
    },
  ];

  if (messages.length === 0 && !loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto">
        <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-rose-200 via-purple-200 to-indigo-200 flex items-center justify-center text-purple-700 mb-4 shadow-lg shadow-purple-100/70 border border-white">
          <Bot className="w-8 h-8 text-purple-700" />
        </div>

        <h2 className="text-xl sm:text-2xl font-bold text-slate-800 mb-1.5 flex items-center justify-center gap-2 tracking-tight">
          RelayAI
          <Sparkles className="w-5 h-5 text-purple-500" />
        </h2>

        <p className="text-xs sm:text-sm font-medium text-purple-700/80 mb-2">
          AI, without the interruption.
        </p>

        <p className="text-xs text-slate-500 max-w-md leading-relaxed mb-8">
          A resilient LLM gateway featuring automatic API key failover, intelligent response caching, and multi-turn session persistence.
        </p>

        {/* Suggestion Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
          {suggestions.map((item, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectPrompt && onSelectPrompt(item.prompt)}
              className="p-3.5 rounded-2xl bg-white/80 hover:bg-white border border-[#EFEAE6] hover:border-purple-200 hover:shadow-md transition-all group flex flex-col justify-between"
            >
              <div className="flex items-center justify-between w-full mb-1">
                <span className="p-1.5 rounded-xl bg-purple-50 border border-purple-100/60">
                  {item.icon}
                </span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-purple-600 group-hover:translate-x-0.5 transition-all" />
              </div>
              <div>
                <div className="text-xs font-semibold text-slate-800 group-hover:text-purple-700 transition-colors">
                  {item.title}
                </div>
                <div className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                  {item.desc}
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 space-y-1">
      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} />
      ))}

      {loading && (
        <div className="flex justify-start my-4">
          <div className="flex items-start gap-2.5 max-w-xl">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-violet-600 to-purple-600 flex items-center justify-center shrink-0 text-white shadow-xs mt-1">
              <Bot className="w-4 h-4" />
            </div>
            <div className="flex items-center gap-2.5 px-4 py-3 rounded-2xl rounded-tl-xs bg-white/95 border border-[#EFEAE6] shadow-sm text-slate-600 text-xs">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-purple-600" />
              <span className="font-medium text-slate-600">Generating resilient response...</span>
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
