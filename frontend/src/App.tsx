import React, { useState, useEffect, useCallback } from 'react';
import { ChatMessage, HealthResponse } from './types/chat';
import { sendChatMessage, getHealth, ApiError } from './services/api';
import { MessageList } from './components/MessageList';
import { ChatInput } from './components/ChatInput';
import { SystemPromptInput } from './components/SystemPromptInput';
import { SimulationControls } from './components/SimulationControls';
import {
  Bot,
  RotateCcw,
  Sparkles,
  AlertCircle,
  Terminal,
} from 'lucide-react';

const generateSessionId = (): string => {
  return `s-${Date.now().toString(36)}-${Math.random().toString(36).substring(2, 7)}`;
};

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(generateSessionId);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [systemPrompt, setSystemPrompt] = useState<string>('');
  const [simulationScenario, setSimulationScenario] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  // Poll or check health on initial mount
  useEffect(() => {
    let mounted = true;
    getHealth()
      .then((data) => {
        if (mounted) setHealth(data);
      })
      .catch((_) => {
        // Backend might still be starting; non-blocking
      });
    return () => {
      mounted = false;
    };
  }, []);

  const handleStartNewSession = useCallback(() => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
    setError(null);
  }, []);

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
    <div className="flex flex-col h-screen w-full bg-slate-950 text-slate-100 font-sans antialiased">
      {/* Top Navigation Bar */}
      <header className="h-16 border-b border-slate-800 bg-slate-900/80 backdrop-blur-md px-4 sm:px-6 flex items-center justify-between shrink-0 z-10">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-600 to-sky-500 flex items-center justify-center text-white shadow-md shadow-cyan-900/30">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="font-bold text-sm sm:text-base text-slate-100 tracking-tight flex items-center gap-1.5">
                RelayAI
              </h1>
              <span className="hidden sm:inline-flex items-center gap-1 text-[10px] font-semibold tracking-wide px-2 py-0.5 rounded-full bg-cyan-950/80 text-cyan-400 border border-cyan-800/60">
                <Sparkles className="w-3 h-3" /> AI, without the interruption.
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <span className="font-mono text-[11px] text-slate-300">
                Session: <span className="text-cyan-300 font-medium">{sessionId}</span>
              </span>
              {health && (
                <span className="hidden md:inline-flex items-center gap-1 text-[11px] text-emerald-400">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  {health.keys_configured} Keys Active
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Failure Simulation Header Dropdown */}
          <SimulationControls
            scenario={simulationScenario}
            onScenarioChange={setSimulationScenario}
            disabled={loading}
          />

          {/* New Session Button */}
          <button
            type="button"
            onClick={handleStartNewSession}
            disabled={loading}
            title="Start a new session (resets conversation history and generates fresh session ID)"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 active:bg-slate-600 border border-slate-700 text-slate-300 hover:text-white text-xs font-medium transition-all shadow-sm disabled:opacity-50"
          >
            <RotateCcw className="w-3.5 h-3.5 text-slate-400 group-hover:rotate-180 transition-transform" />
            <span className="hidden sm:inline">New Session</span>
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex flex-col max-w-4xl w-full mx-auto overflow-hidden p-2 sm:p-4">
        {/* Session System Prompt Configuration Accordion */}
        <div className="mb-2 shrink-0">
          <SystemPromptInput
            systemPrompt={systemPrompt}
            onSystemPromptChange={setSystemPrompt}
            disabled={loading}
          />
        </div>

        {/* Global Error Banner */}
        {error && (
          <div className="mb-2 p-3 bg-red-950/60 border border-red-500/50 rounded-xl text-red-200 text-xs flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-200 text-xs font-semibold underline ml-2"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Message Area */}
        <div className="flex-1 overflow-hidden bg-slate-900/40 border border-slate-800/80 rounded-2xl flex flex-col shadow-inner backdrop-blur-sm">
          <MessageList messages={messages} loading={loading} />
        </div>

        {/* Chat Input Area */}
        <div className="mt-3 shrink-0">
          <ChatInput onSendMessage={handleSendMessage} disabled={loading} />
          <div className="mt-1.5 flex items-center justify-between px-1 text-[11px] text-slate-500">
            <span className="flex items-center gap-1">
              <Terminal className="w-3 h-3 text-slate-600" />
              LiteLLM Proxy &bull; Cache Aware &bull; Zero Token Estimation
            </span>
            <span className="font-mono text-[10px]">
              Turn: {messages.filter((m) => m.role === 'user').length}
            </span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;

