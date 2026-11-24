import React from 'react';
import { ShieldAlert, AlertCircle } from 'lucide-react';

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
      <div className="flex items-center gap-1 text-slate-500 font-medium shrink-0">
        <ShieldAlert className={`w-3.5 h-3.5 ${scenario ? 'text-amber-500 animate-pulse' : 'text-slate-400'}`} />
        <span className="text-[11px] font-semibold text-slate-600">Test Hook:</span>
      </div>

      <select
        value={scenario}
        onChange={(e) => onScenarioChange(e.target.value)}
        disabled={disabled}
        aria-label="Failover Test Scenario"
        className={`px-2.5 py-1.5 rounded-xl text-xs font-mono border transition-all focus:outline-none ${
          scenario
            ? 'bg-amber-50 border-amber-300 text-amber-800 font-semibold shadow-xs'
            : 'bg-white border-slate-200 text-slate-700 hover:border-slate-300'
        }`}
      >
        {scenarios.map((s) => (
          <option key={s.value} value={s.value} className="bg-white text-slate-800">
            {s.label}
          </option>
        ))}
      </select>

      {scenario && (
        <span className="hidden xl:inline-flex items-center gap-1 text-[11px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded-lg border border-amber-200">
          <AlertCircle className="w-3 h-3 text-amber-500" />
          X-Simulate-Failure: {scenario}
        </span>
      )}
    </div>
  );
};
