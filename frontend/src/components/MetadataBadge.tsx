import React from 'react';
import { ChatMetadata } from '../types/chat';
import { Zap, Database, Clock, ArrowDownCircle, ArrowUpCircle, Key } from 'lucide-react';

interface MetadataBadgeProps {
  metadata: ChatMetadata;
}

export const MetadataBadge: React.FC<MetadataBadgeProps> = ({ metadata }) => {
  const isCache = metadata.resolution_source === 'LLM_CACHE';

  return (
    <div className="mt-3 pt-3 border-t border-slate-700/60 text-xs flex flex-wrap items-center gap-2 text-slate-300">
      {/* Resolution Source: strictly LIVE_INFERENCE or LLM_CACHE */}
      <span
        data-testid="meta-source"
        className={`px-2.5 py-1 rounded-full font-semibold flex items-center gap-1.5 shadow-sm ${
          isCache
            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
            : 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
        }`}
      >
        {isCache ? <Database className="w-3.5 h-3.5" /> : <Zap className="w-3.5 h-3.5" />}
        {metadata.resolution_source}
      </span>

      {/* Model Name */}
      <span
        data-testid="meta-model"
        className="px-2.5 py-1 rounded-md bg-slate-800 border border-slate-700 font-mono text-slate-300"
      >
        {metadata.model}
      </span>

      {/* Latency: formatted as e.g. 812 ms */}
      <span
        data-testid="meta-latency"
        className="px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700/80 flex items-center gap-1 text-amber-300 font-mono"
      >
        <Clock className="w-3 h-3" />
        {metadata.latency_ms} ms
      </span>

      {/* Input Tokens */}
      <span className="px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700/80 flex items-center gap-1 text-slate-300 font-mono">
        <ArrowDownCircle className="w-3 h-3 text-sky-400" />
        in: <span data-testid="meta-input-tokens" className="font-semibold text-slate-200">{metadata.input_tokens}</span>
      </span>

      {/* Output Tokens */}
      <span className="px-2 py-1 rounded-md bg-slate-800/80 border border-slate-700/80 flex items-center gap-1 text-slate-300 font-mono">
        <ArrowUpCircle className="w-3 h-3 text-purple-400" />
        out: <span data-testid="meta-output-tokens" className="font-semibold text-slate-200">{metadata.output_tokens}</span>
      </span>

      {/* Key Alias & Failover Tracking (Live Inference only) */}
      {metadata.key_id && (
        <span className="px-2 py-1 rounded-md bg-indigo-950/60 border border-indigo-700/50 flex items-center gap-1 text-indigo-300 font-mono">
          <Key className="w-3 h-3" />
          {metadata.key_id}
          {metadata.fallback_attempts > 0 && (
            <span className="ml-1 text-amber-400 font-semibold">
              (fallback: {metadata.fallback_attempts})
            </span>
          )}
        </span>
      )}
    </div>
  );
};

