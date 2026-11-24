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
    <div className="border border-slate-800 rounded-xl bg-slate-900/60 p-3 text-xs shadow-sm">
      <div className="flex items-center justify-between mb-1.5">
        <span className="flex items-center gap-1.5 font-medium text-slate-300">
          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
          Optional Session System Prompt
          {systemPrompt && <span className="w-2 h-2 rounded-full bg-cyan-400 inline-block ml-1" />}
        </span>
        <span className="text-[10px] text-slate-500 font-mono">multi-turn persona</span>
      </div>

      <input
        type="text"
        data-testid="system-prompt-input"
        value={systemPrompt}
        onChange={(e) => onSystemPromptChange(e.target.value)}
        disabled={disabled}
        placeholder="e.g. You are a concise physics professor explaining concepts simply..."
        className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-cyan-500 text-xs disabled:opacity-50"
      />
      <p className="mt-1 text-[11px] text-slate-500">
        Overrides the default system prompt persona for this session across all conversation turns.
      </p>
    </div>
  );
};
