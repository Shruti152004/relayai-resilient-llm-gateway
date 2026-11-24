/**
 * Frontend TypeScript Type Definitions matching Backend API Contracts.
 */

export type ResolutionSource = "LIVE_INFERENCE" | "LLM_CACHE";

export interface ChatMetadata {
  resolution_source: ResolutionSource;
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  key_id: string | null;
  fallback_attempts: number;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  metadata?: ChatMetadata;
  createdAt?: string;
  isError?: boolean;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  system_prompt?: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  metadata: ChatMetadata;
}

export interface HealthResponse {
  status: string;
  keys_configured: number;
  cache_enabled: boolean;
}

export interface SessionHistoryItem {
  role: "user" | "assistant";
  content: string;
  metadata?: {
    resolution_source: ResolutionSource;
    input_tokens: number;
    output_tokens: number;
  };
}

export interface SessionHistoryResponse {
  session_id: string;
  messages: SessionHistoryItem[];
}

