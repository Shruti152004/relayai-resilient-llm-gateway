/**
 * API Service for communicating with the FastAPI LLM Gateway Backend.
 * Strictly adheres to backend API contracts and does not invent or estimate data.
 */

import { ChatRequest, ChatResponse, HealthResponse, SessionHistoryResponse } from '../types/chat';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string) || '';

export class ApiError extends Error {
  constructor(public statusCode: number, public detail: string) {
    super(detail);
    this.name = 'ApiError';
  }
}

/**
 * Checks backend connectivity and key configuration status.
 */
export async function getHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE_URL}/health`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!res.ok) {
    throw new ApiError(res.status, `Health check failed with status ${res.status}`);
  }

  return res.json();
}

/**
 * Sends a chat message to POST /chat with optional X-Simulate-Failure header.
 */
export async function sendChatMessage(
  payload: ChatRequest,
  simulateFailure?: string | null
): Promise<ChatResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  if (simulateFailure && simulateFailure.trim()) {
    headers['X-Simulate-Failure'] = simulateFailure.trim();
  }

  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      // Parse structured JSON detail
      let detailMsg = 'Request failed';
      if (typeof data.detail === 'string') {
        detailMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        detailMsg = data.detail.map((e: any) => e.msg || JSON.stringify(e)).join('; ');
      }
      throw new ApiError(res.status, detailMsg);
    }

    return data as ChatResponse;
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(500, err.message || 'Network connection to backend failed.');
  }
}

/**
 * Retrieves chronological message history from GET /sessions/{session_id}/messages.
 */
export async function getSessionHistory(sessionId: string): Promise<SessionHistoryResponse> {
  const res = await fetch(`${API_BASE_URL}/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: 'GET',
    headers: { 'Accept': 'application/json' },
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detailMsg = data.detail || `Failed to fetch session history (HTTP ${res.status})`;
    throw new ApiError(res.status, detailMsg);
  }

  return res.json();
}

