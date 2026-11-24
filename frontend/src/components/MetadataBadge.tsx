import React from 'react';
import { ChatMetadata } from '../types/chat';
import { Zap, Database, Clock, ArrowDownCircle, ArrowUpCircle, Key } from 'lucide-react';

interface MetadataBadgeProps {
  metadata: ChatMetadata;
}

export const MetadataBadge: React.FC<MetadataBadgeProps> = ({ metadata }) => {
  const isCache = metadata.resolution_source === 'LLM_CACHE';

  return (
    <div className="mt-2.5 pt-2.5 border-t border-slate-100/90 text-xs flex flex-wrap items-center gap-1.5 text-slate-500">
      {/* Resolution Source: strictly LIVE_INFERENCE or LLM_CACHE */}
      <span
        data-testid="meta-source"
        className={`px-2.5 py-0.5 rounded-full font-semibold text-[11px] flex items-center gap-1 shadow-xs ${
          isCache
            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200/80'
            : 'bg-violet-50 text-violet-700 border border-violet-200/80'
        }`}
      >
        {isCache ? <Database className="w-3 h-3 text-emerald-600" /> : <Zap className="w-3 h-3 text-violet-600" />}
        {metadata.resolution_source}
      </span>

      {/* Model Name */}
      <span
        data-testid="meta-model"
        className="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200/70 font-mono text-[11px] text-slate-700"
      >
        {metadata.model}
      </span>

      {/* Latency: formatted as e.g. 812 ms */}
      <span
        data-testid="meta-latency"
        className="px-2 py-0.5 rounded-md bg-amber-50/70 border border-amber-200/60 flex items-center gap-1 text-amber-700 font-mono text-[11px]"
      >
        <Clock className="w-2.5 h-2.5 text-amber-600" />
        {metadata.latency_ms} ms
      </span>

      {/* Input Tokens */}
      <span className="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200/70 flex items-center gap-1 text-slate-600 font-mono text-[11px]">
        <ArrowDownCircle className="w-2.5 h-2.5 text-sky-500" />
        in: <span data-testid="meta-input-tokens" className="font-semibold text-slate-800">{metadata.input_tokens}</span>
      </span>

      {/* Output Tokens */}
      <span className="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200/70 flex items-center gap-1 text-slate-600 font-mono text-[11px]">
        <ArrowUpCircle className="w-2.5 h-2.5 text-purple-500" />
        out: <span data-testid="meta-output-tokens" className="font-semibold text-slate-800">{metadata.output_tokens}</span>
      </span>

      {/* Key Alias & Failover Tracking (Live Inference only) */}
      {metadata.key_id && (
        <span className="px-2 py-0.5 rounded-md bg-indigo-50 border border-indigo-200/70 flex items-center gap-1 text-indigo-700 font-mono text-[11px]">
          <Key className="w-2.5 h-2.5 text-indigo-600" />
          {metadata.key_id}
          {metadata.fallback_attempts > 0 && (
            <span className="ml-1 text-rose-600 font-semibold">
              (fallback: {metadata.fallback_attempts})
            </span>
          )}
        </span>
      )}
    </div>
  );
};
