import React from 'react';
import { Sliders } from 'lucide-react';

interface SystemPromptInputProps {
  systemPrompt: string;
  onSystemPromptChange: (val: string) => void;
  disabled: boolean;
}

export const SystemPromptInput: React.FC<SystemPromptInputProps> = ({
  systemPrompt,
  onSystemPromptChange,
  disabled,
}) => {
  return (
    <div className="border border-[#EFEAE6] rounded-2xl bg-white/90 p-3.5 text-xs shadow-xs">
      <div className="flex items-center justify-between mb-1.5">
        <span className="flex items-center gap-1.5 font-semibold text-slate-700">
          <Sliders className="w-3.5 h-3.5 text-purple-600" />
          Session System Prompt
          {systemPrompt && <span className="w-2 h-2 rounded-full bg-purple-500 inline-block ml-0.5" />}
        </span>
        <span className="text-[10px] text-slate-400 font-mono bg-slate-50 px-2 py-0.5 rounded-full border border-slate-100">
          multi-turn persona
        </span>
      </div>

      <input
        type="text"
        data-testid="system-prompt-input"
        value={systemPrompt}
        onChange={(e) => onSystemPromptChange(e.target.value)}
        disabled={disabled}
        placeholder="e.g. You are a concise physics professor explaining concepts simply..."
        className="w-full px-3 py-2 bg-slate-50/70 border border-slate-200/80 rounded-xl text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-purple-400 text-xs disabled:opacity-50 transition-colors"
      />
      <p className="mt-1 text-[11px] text-slate-400 leading-tight">
        Customizes the AI persona and context across all turns in this session.
      </p>
    </div>
  );
};
