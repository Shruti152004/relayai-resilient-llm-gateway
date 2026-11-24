import React, { useState, KeyboardEvent } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [input, setInput] = useState('');

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;

    // Call callback with message
    onSendMessage(trimmed);

    // Strictly empty input field after sending as mandated by PDF contract
    setInput('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative flex items-end gap-2">
      <textarea
        data-testid="chat-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Type a message... (Press Enter to send)"
        disabled={disabled}
        rows={1}
        className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500 focus:border-transparent resize-none text-sm leading-relaxed disabled:opacity-50 disabled:cursor-not-allowed shadow-inner min-h-[48px] max-h-32"
      />
      <button
        type="submit"
        data-testid="send-button"
        disabled={disabled || !input.trim()}
        className="h-12 px-5 bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 disabled:from-slate-700 disabled:to-slate-800 text-white rounded-xl font-medium flex items-center justify-center gap-1.5 transition-all shadow-md disabled:cursor-not-allowed shrink-0"
      >
        {disabled ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <>
            <span className="hidden sm:inline text-xs font-semibold">Send</span>
            <Send className="w-4 h-4" />
          </>
        )}
      </button>
    </form>
  );
};

