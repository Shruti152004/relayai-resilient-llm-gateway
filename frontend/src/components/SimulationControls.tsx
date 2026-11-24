import React from 'react';
import { AlertCircle, ShieldAlert } from 'lucide-react';

interface SimulationControlsProps {
  scenario: string;
  onScenarioChange: (scenario: string) => void;
  disabled: boolean;
}

export const SimulationControls: React.FC<SimulationControlsProps> = ({
  scenario,
  onScenarioChange,
  disabled,
}) => {
  const scenarios = [
    { value: '', label: 'None (Standard Execution)' },
    { value: 'key_1=429', label: 'Simulate key_1 = 429 (Rate Limit Failover)' },
    { value: 'key_1=500', label: 'Simulate key_1 = 500 (Server Error Failover)' },
    { value: 'key_1=429,key_2=500', label: 'Simulate key_1=429, key_2=500 (Multi-Key Failover)' },
    { value: '*=429', label: 'Simulate *=429 (Total Outage -> 503)' },
  ];

  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="flex items-center gap-1 text-slate-400 font-medium shrink-0">
        <ShieldAlert className={`w-3.5 h-3.5 ${scenario ? 'text-amber-400 animate-pulse' : 'text-slate-500'}`} />
        <span className="hidden md:inline">Test Hook:</span>
      </div>

      <select
        value={scenario}
        onChange={(e) => onScenarioChange(e.target.value)}
        disabled={disabled}
        aria-label="Failover Test Scenario"
        className={`px-2.5 py-1.5 rounded-lg text-xs font-mono border transition-all focus:outline-none ${
          scenario
            ? 'bg-amber-950/40 border-amber-500/50 text-amber-300 font-semibold'
            : 'bg-slate-800 border-slate-700 text-slate-300'
        }`}
      >
        {scenarios.map((s) => (
          <option key={s.value} value={s.value} className="bg-slate-900 text-slate-200">
            {s.label}
          </option>
        ))}
      </select>

      {scenario && (
        <span className="hidden lg:inline-flex items-center gap-1 text-[11px] text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
          <AlertCircle className="w-3 h-3" />
          X-Simulate-Failure: {scenario}
        </span>
      )}
    </div>
  );
};

