import React from 'react';
import { ChatMessage } from '../types/chat';
import { MetadataBadge } from './MetadataBadge';
import { User, Bot, AlertTriangle } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  if (message.isError) {
    return (
      <div className="flex items-start gap-3 my-3 p-4 rounded-xl bg-red-950/40 border border-red-500/40 text-red-200 max-w-2xl mx-auto shadow-md">
        <AlertTriangle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
        <div className="text-sm">
          <div className="font-semibold text-red-300 mb-1">Request Error</div>
          <div className="text-red-200/90 whitespace-pre-wrap">{message.content}</div>
        </div>
      </div>
    );
  }

  if (message.role === 'user') {
    return (
      <div className="flex justify-end my-3">
        <div className="flex items-start gap-2.5 max-w-xl">
          <div className="bg-sky-600 text-white px-4 py-3 rounded-2xl rounded-tr-none shadow-md text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
          <div className="w-8 h-8 rounded-full bg-sky-700 flex items-center justify-center shrink-0 text-white shadow-sm">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message (strictly wraps reply and metadata within assistant-message)
  return (
    <div className="flex justify-start my-3">
      <div
        data-testid="assistant-message"
        className="flex items-start gap-2.5 max-w-2xl"
      >
        <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center shrink-0 text-cyan-400 shadow-sm mt-1">
          <Bot className="w-4 h-4" />
        </div>
        <div className="bg-slate-800/90 border border-slate-700 px-4 py-3.5 rounded-2xl rounded-tl-none shadow-md text-sm leading-relaxed text-slate-100 w-full">
          <div className="whitespace-pre-wrap">{message.content}</div>
          {message.metadata && <MetadataBadge metadata={message.metadata} />}
        </div>
      </div>
    </div>
  );
};

