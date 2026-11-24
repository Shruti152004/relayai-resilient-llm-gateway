import React, { useState, KeyboardEvent, useRef, useEffect } from 'react';
import { Send, Loader2, Paperclip } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled: boolean;
  initialValue?: string;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled, initialValue }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (initialValue) {
      setInput(initialValue);
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  }, [initialValue]);

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
    <form
      onSubmit={handleSubmit}
      className="relative flex items-center gap-2 p-2 rounded-2xl bg-white/95 backdrop-blur-xl border border-[#E8E2DE] shadow-[0_10px_35px_rgba(0,0,0,0.05)] focus-within:border-purple-300 focus-within:shadow-[0_10px_35px_rgba(168,85,247,0.08)] transition-all"
    >
      {/* Decorative visual attachment icon (purely visual aesthetic, non-interactive) */}
      <span
        aria-hidden="true"
        title="Decorative visual (RelayAI processes text queries only)"
        className="p-2 text-slate-300 rounded-xl shrink-0 cursor-default select-none pointer-events-none"
      >
        <Paperclip className="w-4 h-4 text-slate-300" />
      </span>

      <textarea
        ref={textareaRef}
        data-testid="chat-input"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask RelayAI anything or enter a prompt..."
        disabled={disabled}
        rows={1}
        className="w-full py-1.5 px-1 bg-transparent text-slate-800 placeholder-slate-400 focus:outline-none resize-none text-sm leading-relaxed disabled:opacity-50 disabled:cursor-not-allowed max-h-32"
      />

      <button
        type="submit"
        data-testid="send-button"
        disabled={disabled || !input.trim()}
        className="h-10 px-4 bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 disabled:from-slate-200 disabled:to-slate-200 text-white disabled:text-slate-400 rounded-xl font-medium flex items-center justify-center gap-1.5 transition-all shadow-sm shadow-purple-200/50 disabled:shadow-none disabled:cursor-not-allowed shrink-0"
      >
        {disabled ? (
          <Loader2 className="w-4 h-4 animate-spin text-white" />
        ) : (
          <>
            <span className="hidden sm:inline text-xs font-semibold">Send</span>
            <Send className="w-3.5 h-3.5" />
          </>
        )}
      </button>
    </form>
  );
};
