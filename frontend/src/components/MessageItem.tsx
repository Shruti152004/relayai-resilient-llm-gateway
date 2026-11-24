import React from 'react';
import { ChatMessage } from '../types/chat';
import { MetadataBadge } from './MetadataBadge';
import { User, Bot, AlertTriangle } from 'lucide-react';

interface MessageItemProps {
  message: ChatMessage;
}

export const MessageItem: React.FC<MessageItemProps> = ({ message }) => {
  const formatTime = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  if (message.isError) {
    return (
      <div className="flex items-start gap-3 my-3 p-4 rounded-2xl bg-rose-50/80 border border-rose-200/80 text-rose-900 max-w-2xl mx-auto shadow-sm">
        <AlertTriangle className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" />
        <div className="text-sm">
          <div className="font-semibold text-rose-800 mb-0.5">Request Interruption</div>
          <div className="text-rose-700/90 whitespace-pre-wrap leading-relaxed">{message.content}</div>
        </div>
      </div>
    );
  }

  if (message.role === 'user') {
    return (
      <div className="flex justify-end my-4">
        <div className="flex items-start gap-2.5 max-w-xl">
          <div className="flex flex-col items-end">
            <div className="bg-gradient-to-r from-violet-600 via-purple-600 to-indigo-600 text-white px-5 py-3.5 rounded-2xl rounded-tr-xs shadow-sm shadow-indigo-100 text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </div>
            {message.createdAt && (
              <span className="text-[10px] text-slate-400 mt-1 mr-1">
                {formatTime(message.createdAt)}
              </span>
            )}
          </div>
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-rose-400 to-pink-500 flex items-center justify-center shrink-0 text-white shadow-xs">
            <User className="w-4 h-4" />
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message (strictly wraps reply and metadata within assistant-message)
  return (
    <div className="flex justify-start my-4">
      <div
        data-testid="assistant-message"
        className="flex items-start gap-2.5 max-w-2xl w-full"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-violet-600 to-purple-600 flex items-center justify-center shrink-0 text-white shadow-xs mt-1">
          <Bot className="w-4 h-4" />
        </div>
        <div className="flex flex-col w-full">
          <div className="bg-white/95 border border-[#EFEAE6] px-5 py-4 rounded-2xl rounded-tl-xs shadow-[0_4px_20px_rgba(0,0,0,0.02)] text-sm leading-relaxed text-slate-800 w-full">
            <div className="whitespace-pre-wrap">{message.content}</div>
            {message.metadata && <MetadataBadge metadata={message.metadata} />}
          </div>
          {message.createdAt && (
            <span className="text-[10px] text-slate-400 mt-1 ml-1">
              {formatTime(message.createdAt)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
};
