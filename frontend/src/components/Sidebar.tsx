import React from 'react';
import {
  Bot,
  Plus,
  MessageSquare,
  Sliders,
  PanelLeftClose,
  PanelLeft,
  Sparkles,
} from 'lucide-react';
import { HealthResponse } from '../types/chat';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  currentSessionId: string;
  sessionList: string[];
  onSelectSession: (sessionId: string) => void;
  onNewSession: () => void;
  health: HealthResponse | null;
  onOpenSettings: () => void;
  isSettingsOpen: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onToggle,
  currentSessionId,
  sessionList,
  onSelectSession,
  onNewSession,
  health,
  onOpenSettings,
  isSettingsOpen,
}) => {
  return (
    <aside
      className={`relative flex flex-col h-full bg-[#FCFAF8]/90 backdrop-blur-xl border-r border-[#EFEAE6] transition-all duration-300 ease-in-out shrink-0 z-20 ${
        isOpen ? 'w-64' : 'w-16'
      }`}
    >
      {/* Top Header / Brand */}
      <div className="h-16 flex items-center justify-between px-3.5 border-b border-[#EFEAE6]/80">
        <div className="flex items-center gap-2.5 overflow-hidden">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-violet-600 via-purple-500 to-rose-400 flex items-center justify-center text-white shadow-sm shadow-purple-200 shrink-0">
            <Bot className="w-5 h-5" />
          </div>
          {isOpen && (
            <div className="flex flex-col overflow-hidden">
              <span className="font-bold text-sm text-slate-800 tracking-tight flex items-center gap-1">
                RelayAI
                <Sparkles className="w-3 h-3 text-purple-500" />
              </span>
              <span className="text-[10px] text-slate-400 truncate font-medium">
                AI, without the interruption.
              </span>
            </div>
          )}
        </div>

        <button
          type="button"
          onClick={onToggle}
          title={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100/80 transition-colors shrink-0"
        >
          {isOpen ? <PanelLeftClose className="w-4 h-4" /> : <PanelLeft className="w-4 h-4" />}
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          type="button"
          onClick={onNewSession}
          className={`w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-500 hover:to-purple-500 active:scale-[0.99] text-white text-xs font-semibold shadow-sm shadow-violet-200 transition-all ${
            !isOpen ? 'px-0' : ''
          }`}
          title="New Chat Session"
        >
          <Plus className="w-4 h-4 shrink-0" />
          {isOpen && <span>New Chat</span>}
        </button>
      </div>

      {/* Session History */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        {isOpen && (
          <div className="px-2 pb-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
            Conversations
          </div>
        )}

        {sessionList.map((sId) => {
          const isSelected = sId === currentSessionId;
          return (
            <button
              key={sId}
              type="button"
              onClick={() => onSelectSession(sId)}
              title={`Session ${sId}`}
              className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs transition-all text-left ${
                isSelected
                  ? 'bg-white text-violet-700 font-medium shadow-xs border border-violet-100'
                  : 'text-slate-600 hover:bg-white/60 hover:text-slate-900'
              }`}
            >
              <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${isSelected ? 'text-violet-600' : 'text-slate-400'}`} />
              {isOpen && (
                <div className="flex-1 truncate">
                  <span className="font-mono text-[11px] truncate block">{sId}</span>
                </div>
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Actions & Settings */}
      <div className="p-3 border-t border-[#EFEAE6]/80 space-y-1 bg-[#FAF7F5]/50">
        <button
          type="button"
          onClick={onOpenSettings}
          title="Session & Simulation Settings"
          className={`w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs transition-colors text-left ${
            isSettingsOpen
              ? 'bg-purple-100/70 text-purple-800 font-medium'
              : 'text-slate-600 hover:bg-white/80 hover:text-slate-900'
          }`}
        >
          <Sliders className="w-4 h-4 text-purple-500 shrink-0" />
          {isOpen && <span className="font-medium">Session Settings</span>}
        </button>

        {/* Backend Status indicator */}
        <div className={`flex items-center gap-2 px-2.5 py-1.5 text-[11px] text-slate-500 ${!isOpen ? 'justify-center' : ''}`}>
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          {isOpen && (
            <span className="truncate">
              {health ? `${health.keys_configured} Keys Active` : 'Gateway Ready'}
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};
