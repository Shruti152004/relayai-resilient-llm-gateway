import React, { useRef, useEffect } from 'react';
import { ChatMessage } from '../types/chat';
import { MessageItem } from './MessageItem';
import { Bot, Sparkles, Loader2 } from 'lucide-react';

interface MessageListProps {
  messages: ChatMessage[];
  loading: boolean;
}

export const MessageList: React.FC<MessageListProps> = ({ messages, loading }) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  if (messages.length === 0 && !loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 text-slate-400">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-cyan-600/20 to-sky-500/20 border border-cyan-500/40 flex items-center justify-center text-cyan-400 mb-4 shadow-lg shadow-cyan-950/40">
          <Bot className="w-8 h-8 text-cyan-400" />
        </div>
        <h3 className="text-base font-bold text-slate-100 mb-1 flex items-center gap-2">
          RelayAI
          <Sparkles className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-normal text-cyan-400">&bull; AI, without the interruption.</span>
        </h3>
        <p className="max-w-md text-xs text-slate-400 leading-relaxed">
          A resilient LLM gateway featuring API key failover, intelligent response caching, and multi-turn chat session management.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-2">
      {messages.map((msg) => (
        <MessageItem key={msg.id} message={msg} />
      ))}

      {loading && (
        <div className="flex justify-start my-3">
          <div className="flex items-center gap-2.5 px-4 py-3 rounded-2xl rounded-tl-none bg-slate-800/80 border border-slate-700/60 text-slate-400 text-xs">
            <Loader2 className="w-4 h-4 animate-spin text-cyan-400" />
            <span>Generating response with active key...</span>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};

