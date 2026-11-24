import React, { useState, useEffect, useCallback } from 'react';
import { ChatMessage, HealthResponse } from './types/chat';
import { sendChatMessage, getHealth, ApiError } from './services/api';
import { Sidebar } from './components/Sidebar';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { SystemPromptInput } from './components/SystemPromptInput';
import { SimulationControls } from './components/SimulationControls';
import {
  RotateCcw,
  Sparkles,
  AlertCircle,
  Terminal,
  Sliders,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';

const generateSessionId = (): string => {
  return `s-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`;
};

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(generateSessionId);
  const [sessionList, setSessionList] = useState<string[]>(() => [sessionId]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [systemPrompt, setSystemPrompt] = useState<string>('');
  const [simulationScenario, setSimulationScenario] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState<boolean>(true);
  const [isPromptDrawerOpen, setIsPromptDrawerOpen] = useState<boolean>(false);
  const [suggestedPrompt, setSuggestedPrompt] = useState<string>('');

  // Initial health check
  useEffect(() => {
    let mounted = true;
    getHealth()
      .then((data) => {
        if (mounted) setHealth(data);
      })
      .catch((_) => {
        // Backend non-blocking check
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleStartNewSession = useCallback(() => {
    const newId = generateSessionId();
    setSessionId(newId);
    setSessionList((prev) => (prev.includes(newId) ? prev : [newId, ...prev]));
    setMessages([]);
    setError(null);
    setSuggestedPrompt('');
  }, []);

  const handleSelectSession = useCallback((id: string) => {
    setSessionId(id);
    setError(null);
  }, []);

  const handleSelectPrompt = (prompt: string) => {
    setSuggestedPrompt(prompt);
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `usr-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
      role: 'user',
      content: text.trim(),
      createdAt: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);
    setError(null);
    setSuggestedPrompt('');

    try {
      const response = await sendChatMessage(
        {
          session_id: sessionId,
          message: text.trim(),
          system_prompt: systemPrompt.trim() ? systemPrompt.trim() : undefined,
        },
        simulationScenario || null
      );

      const assistantMessage: ChatMessage = {
        id: `asst-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
        role: 'assistant',
        content: response.reply,
        metadata: response.metadata,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      const errorMsg =
        err instanceof ApiError
          ? `[HTTP ${err.statusCode}] ${err.detail}`
          : err.message || 'An unexpected communication error occurred.';

      setError(errorMsg);

      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}-${Math.random().toString(36).substring(2, 5)}`,
        role: 'assistant',
        content: errorMsg,
        isError: true,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full bg-[#FAF8F5] text-slate-800 font-sans antialiased overflow-hidden">
      {/* Slim Vertical Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen((prev) => !prev)}
        currentSessionId={sessionId}
        sessionList={sessionList}
        onSelectSession={handleSelectSession}
        onNewSession={handleStartNewSession}
        health={health}
        onOpenSettings={() => setIsPromptDrawerOpen((prev) => !prev)}
        isSettingsOpen={isPromptDrawerOpen}
      />

      {/* Main App Container */}
      <div className="flex-1 flex flex-col h-full overflow-hidden bg-gradient-to-br from-[#FAF8F5] via-[#FFFDFB] to-[#F5F2F9]">
        {/* Top Header Bar */}
        <header className="h-16 border-b border-[#EFEAE6]/90 bg-white/70 backdrop-blur-xl px-4 sm:px-6 flex items-center justify-between shrink-0 z-10">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="font-bold text-sm text-slate-800 tracking-tight">
                RelayAI
              </span>
              <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200/60">
                <Sparkles className="w-3 h-3 text-purple-500" /> AI, without the interruption.
              </span>
            </div>

            <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white border border-slate-200/80 text-[11px] font-mono text-slate-600 shadow-2xs">
              <span className="text-slate-400">Session:</span>
              <span className="text-purple-700 font-semibold">{sessionId}</span>
            </span>
          </div>

          <div className="flex items-center gap-2 sm:gap-3">
            {/* Failure Simulation Test Hook Header Dropdown */}
            <SimulationControls
              scenario={simulationScenario}
              onScenarioChange={setSimulationScenario}
              disabled={loading}
            />

            {/* System Prompt Toggle Pill */}
            <button
              type="button"
              onClick={() => setIsPromptDrawerOpen((prev) => !prev)}
              title="Toggle System Prompt Drawer"
              className={`flex items-center gap-1 px-2.5 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                isPromptDrawerOpen || systemPrompt
                  ? 'bg-purple-50 border-purple-200 text-purple-700 shadow-xs'
                  : 'bg-white border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              <Sliders className="w-3.5 h-3.5 text-purple-500" />
              <span className="hidden sm:inline">Persona</span>
              {isPromptDrawerOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            </button>

            {/* New Session Quick Button */}
            <button
              type="button"
              onClick={handleStartNewSession}
              disabled={loading}
              title="Start a new session"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium transition-all shadow-2xs disabled:opacity-50"
            >
              <RotateCcw className="w-3.5 h-3.5 text-slate-400" />
              <span className="hidden sm:inline">New Session</span>
            </button>
          </div>
        </header>

        {/* Central Chat & Messages Area */}
        <main className="flex-1 flex flex-col w-full max-w-4xl mx-auto overflow-hidden px-3 sm:px-6 pt-3 pb-2 relative">
          {/* System Prompt Accordion / Card (Always kept in DOM for required testid contract) */}
          <div className={`mb-3 shrink-0 transition-all ${isPromptDrawerOpen ? 'block' : 'hidden md:block'}`}>
            <SystemPromptInput
              systemPrompt={systemPrompt}
              onSystemPromptChange={setSystemPrompt}
              disabled={loading}
            />
          </div>

          {/* Global Error Notification */}
          {error && (
            <div className="mb-3 p-3.5 bg-rose-50/90 border border-rose-200 rounded-2xl text-rose-800 text-xs flex items-center justify-between shrink-0 shadow-sm">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
                <span>{error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-rose-600 hover:text-rose-800 text-xs font-semibold underline ml-2"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Central Message Stream */}
          <div className="flex-1 overflow-hidden bg-white/70 backdrop-blur-md border border-[#EFEAE6] rounded-3xl flex flex-col shadow-[0_8px_30px_rgba(0,0,0,0.02)]">
            <MessageList
              messages={messages}
              loading={loading}
              onSelectPrompt={handleSelectPrompt}
            />
          </div>

          {/* Floating Rounded Input Composer */}
          <div className="mt-3 shrink-0">
            <ChatInput
              onSendMessage={handleSendMessage}
              disabled={loading}
              initialValue={suggestedPrompt}
            />

            <div className="mt-2 flex items-center justify-between px-2 text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5">
                <Terminal className="w-3 h-3 text-slate-400" />
                <span>LiteLLM Proxy &bull; Cache Aware &bull; Zero Token Estimation</span>
              </span>
              <span className="font-mono text-[10px] text-slate-500">
                Turn {messages.filter((m) => m.role === 'user').length}
              </span>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default App;
