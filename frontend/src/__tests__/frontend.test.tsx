import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import App from '../App';
import { MetadataBadge } from '../components/MetadataBadge';
import { ChatInput } from '../components/ChatInput';
import { SimulationControls } from '../components/SimulationControls';
import * as api from '../services/api';
import { ChatMetadata } from '../types/chat';

// Mock scrollIntoView
window.HTMLElement.prototype.scrollIntoView = vi.fn();

describe('Stage 6 Frontend Verification', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('Required data-testid Elements and Baseline Render', () => {
    it('renders chat-input, send-button, and system-prompt-input on page load', async () => {
      vi.spyOn(api, 'getHealth').mockResolvedValue({
        status: 'healthy',
        keys_configured: 2,
        cache_enabled: true,
      });

      render(<App />);

      await waitFor(() => {
        expect(screen.getByTestId('chat-input')).toBeInTheDocument();
      });
      expect(screen.getByTestId('send-button')).toBeInTheDocument();
      expect(screen.getByTestId('system-prompt-input')).toBeInTheDocument();
    });
  });

  describe('ChatInput Component Contracts', () => {
    it('clears chat-input upon sending and disables submission when empty', () => {
      const handleSend = vi.fn();
      render(<ChatInput onSendMessage={handleSend} disabled={false} />);

      const input = screen.getByTestId('chat-input') as HTMLTextAreaElement;
      const sendBtn = screen.getByTestId('send-button');

      // Empty submission should not call handleSend
      fireEvent.click(sendBtn);
      expect(handleSend).not.toHaveBeenCalled();

      // Type and submit
      fireEvent.change(input, { target: { value: 'Hello RelayAI' } });
      expect(input.value).toBe('Hello RelayAI');

      fireEvent.click(sendBtn);
      expect(handleSend).toHaveBeenCalledWith('Hello RelayAI');
      // Strictly emptied
      expect(input.value).toBe('');
    });

    it('submits on Enter keypress (without shift)', () => {
      const handleSend = vi.fn();
      render(<ChatInput onSendMessage={handleSend} disabled={false} />);

      const input = screen.getByTestId('chat-input') as HTMLTextAreaElement;
      fireEvent.change(input, { target: { value: 'Testing enter submit' } });
      fireEvent.keyDown(input, { key: 'Enter', shiftKey: false });

      expect(handleSend).toHaveBeenCalledWith('Testing enter submit');
      expect(input.value).toBe('');
    });
  });

  describe('MetadataBadge & Assistant Message Test IDs', () => {
    it('renders LIVE_INFERENCE metadata with exact required data-testids', () => {
      const liveMeta: ChatMetadata = {
        resolution_source: 'LIVE_INFERENCE',
        model: 'gemini/gemini-2.0-flash',
        latency_ms: 450,
        input_tokens: 42,
        output_tokens: 18,
        key_id: 'key_1',
        fallback_attempts: 0,
      };

      render(<MetadataBadge metadata={liveMeta} />);

      const sourceElem = screen.getByTestId('meta-source');
      expect(sourceElem).toBeInTheDocument();
      expect(sourceElem.textContent).toContain('LIVE_INFERENCE');

      const modelElem = screen.getByTestId('meta-model');
      expect(modelElem).toBeInTheDocument();
      expect(modelElem.textContent).toBe('gemini/gemini-2.0-flash');

      const latencyElem = screen.getByTestId('meta-latency');
      expect(latencyElem).toBeInTheDocument();
      expect(latencyElem.textContent).toContain('450 ms');

      const inTokenElem = screen.getByTestId('meta-input-tokens');
      expect(inTokenElem).toBeInTheDocument();
      expect(inTokenElem.textContent).toBe('42');

      const outTokenElem = screen.getByTestId('meta-output-tokens');
      expect(outTokenElem).toBeInTheDocument();
      expect(outTokenElem.textContent).toBe('18');
    });

    it('renders LLM_CACHE metadata correctly with exact required data-testids', () => {
      const cacheMeta: ChatMetadata = {
        resolution_source: 'LLM_CACHE',
        model: 'gemini/gemini-2.0-flash',
        latency_ms: 12,
        input_tokens: 42,
        output_tokens: 18,
        key_id: null,
        fallback_attempts: 0,
      };

      render(<MetadataBadge metadata={cacheMeta} />);

      const sourceElem = screen.getByTestId('meta-source');
      expect(sourceElem).toBeInTheDocument();
      expect(sourceElem.textContent).toContain('LLM_CACHE');

      expect(screen.getByTestId('meta-model').textContent).toBe('gemini/gemini-2.0-flash');
      expect(screen.getByTestId('meta-latency').textContent).toContain('12 ms');
      expect(screen.getByTestId('meta-input-tokens').textContent).toBe('42');
      expect(screen.getByTestId('meta-output-tokens').textContent).toBe('18');
    });
  });

  describe('Full Multi-Turn Chat Flow & assistant-message testid', () => {
    it('sends message, renders assistant-message and preserves session_id', async () => {
      vi.spyOn(api, 'getHealth').mockResolvedValue({
        status: 'healthy',
        keys_configured: 2,
        cache_enabled: true,
      });

      const sendChatSpy = vi.spyOn(api, 'sendChatMessage').mockResolvedValue({
        session_id: 'test-session-123',
        reply: 'I am the RelayAI assistant.',
        metadata: {
          resolution_source: 'LIVE_INFERENCE',
          model: 'gemini/gemini-2.0-flash',
          latency_ms: 380,
          input_tokens: 25,
          output_tokens: 10,
          key_id: 'key_1',
          fallback_attempts: 0,
        },
      });

      render(<App />);

      const input = screen.getByTestId('chat-input');
      const sendBtn = screen.getByTestId('send-button');

      fireEvent.change(input, { target: { value: 'What is your status?' } });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(screen.getByTestId('assistant-message')).toBeInTheDocument();
      });

      expect(screen.getByText('I am the RelayAI assistant.')).toBeInTheDocument();
      expect(screen.getByTestId('meta-source').textContent).toContain('LIVE_INFERENCE');
      expect(screen.getByTestId('meta-input-tokens').textContent).toBe('25');
      expect(screen.getByTestId('meta-output-tokens').textContent).toBe('10');

      expect(sendChatSpy).toHaveBeenCalledTimes(1);
      const calledPayload = sendChatSpy.mock.calls[0][0];
      expect(calledPayload.message).toBe('What is your status?');
      expect(calledPayload.session_id).toMatch(/^s-/);
    });
  });

  describe('Simulation Controls & X-Simulate-Failure Header', () => {
    it('SimulationControls exposes all required failure simulation scenarios', () => {
      const handleScenario = vi.fn();
      render(<SimulationControls scenario="" onScenarioChange={handleScenario} disabled={false} />);

      const select = screen.getByLabelText('Failover Test Scenario') as HTMLSelectElement;
      expect(select).toBeInTheDocument();

      const options = Array.from(select.options).map((o) => o.value);
      expect(options).toContain('');
      expect(options).toContain('key_1=429');
      expect(options).toContain('key_1=500');
      expect(options).toContain('key_1=429,key_2=500');
      expect(options).toContain('*=429');
    });

    it('api.sendChatMessage sets X-Simulate-Failure header when provided', async () => {
      const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValue({
        ok: true,
        json: async () => ({
          session_id: 'sim-session',
          reply: 'Fallback succeeded with key_2',
          metadata: {
            resolution_source: 'LIVE_INFERENCE',
            model: 'gemini/gemini-2.0-flash',
            latency_ms: 800,
            input_tokens: 30,
            output_tokens: 12,
            key_id: 'key_2',
            fallback_attempts: 1,
          },
        }),
      } as any);

      await api.sendChatMessage(
        { session_id: 'sim-session', message: 'Trigger failover' },
        'key_1=429'
      );

      expect(fetchSpy).toHaveBeenCalledTimes(1);
      const callArgs = fetchSpy.mock.calls[0];
      const headers = callArgs[1]?.headers as Record<string, string>;
      expect(headers['X-Simulate-Failure']).toBe('key_1=429');
    });
  });

  describe('System Prompt Input & Persistence', () => {
    it('includes optional system_prompt in POST payload when filled', async () => {
      const sendChatSpy = vi.spyOn(api, 'sendChatMessage').mockResolvedValue({
        session_id: 'sys-session',
        reply: 'Ahoy matey!',
        metadata: {
          resolution_source: 'LIVE_INFERENCE',
          model: 'gemini/gemini-2.0-flash',
          latency_ms: 350,
          input_tokens: 35,
          output_tokens: 8,
          key_id: 'key_1',
          fallback_attempts: 0,
        },
      });

      render(<App />);

      const sysInput = screen.getByTestId('system-prompt-input');
      fireEvent.change(sysInput, { target: { value: 'Speak like a pirate' } });

      const chatInput = screen.getByTestId('chat-input');
      const sendBtn = screen.getByTestId('send-button');

      fireEvent.change(chatInput, { target: { value: 'Hello' } });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(sendChatSpy).toHaveBeenCalledTimes(1);
      });

      const payload = sendChatSpy.mock.calls[0][0];
      expect(payload.system_prompt).toBe('Speak like a pirate');
    });
  });

  describe('Error Handling Without Crashing', () => {
    it('displays API error clearly without crashing UI when backend fails', async () => {
      vi.spyOn(api, 'sendChatMessage').mockRejectedValue(
        new api.ApiError(503, 'all providers unavailable')
      );

      render(<App />);

      const chatInput = screen.getByTestId('chat-input');
      const sendBtn = screen.getByTestId('send-button');

      fireEvent.change(chatInput, { target: { value: 'Fail this please' } });
      fireEvent.click(sendBtn);

      await waitFor(() => {
        expect(screen.getAllByText(/all providers unavailable/i).length).toBeGreaterThan(0);
      });

      // App remains functional; input is re-enabled
      expect(screen.getByTestId('chat-input')).toBeEnabled();
      expect(screen.getByTestId('send-button')).toBeInTheDocument();
    });
  });
});
