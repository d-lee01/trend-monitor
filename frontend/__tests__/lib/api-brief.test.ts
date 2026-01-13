/**
 * Tests for generateTrendBrief API method (Story 4.2)
 * Covers success, error cases, timeout, and caching scenarios
 */

import { api, APIError } from '@/lib/api';
import { BriefResponse } from '@/lib/types';

// Mock fetch globally
global.fetch = jest.fn();

describe('api.generateTrendBrief', () => {
  const mockToken = 'test-jwt-token';
  const mockTrendId = '123e4567-e89b-12d3-a456-426614174000';
  const mockBriefResponse: BriefResponse = {
    ai_brief: 'This is a test trend. It is trending because of XYZ. It is popular on Reddit and YouTube.',
    generated_at: '2026-01-13T10:00:00Z',
    cached: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it('should successfully generate trend brief with correct request format', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockBriefResponse,
    });

    const result = await api.generateTrendBrief(mockToken, mockTrendId);

    expect(global.fetch).toHaveBeenCalledWith(
      `http://localhost:8000/trends/${mockTrendId}/explain`,
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${mockToken}`,
          'Content-Type': 'application/json',
        },
        signal: expect.any(AbortSignal),
      })
    );

    expect(result).toEqual(mockBriefResponse);
    expect(result.ai_brief).toBe(mockBriefResponse.ai_brief);
    expect(result.cached).toBe(false);
  });

  it('should return cached brief response when cached=true', async () => {
    const cachedResponse: BriefResponse = {
      ...mockBriefResponse,
      cached: true,
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => cachedResponse,
    });

    const result = await api.generateTrendBrief(mockToken, mockTrendId);

    expect(result.cached).toBe(true);
    expect(result.ai_brief).toBe(mockBriefResponse.ai_brief);
  });

  it('should throw APIError 401 on authentication failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(401, 'Authentication failed. Please log in again.'));
  });

  it('should throw APIError 404 when trend not found', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(404, 'Trend not found.'));
  });

  it('should throw APIError 503 on Claude API failure', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 503,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(503, 'Unable to generate explanation. Please try again later.'));
  });

  it('should throw APIError 429 on rate limit exceeded', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 429,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(429, 'Rate limit exceeded. Please try again later.'));
  });

  it('should timeout after 2 seconds and throw APIError 408', async () => {
    // Mock fetch to reject with AbortError when aborted
    const mockAbortError = new Error('The operation was aborted');
    mockAbortError.name = 'AbortError';

    (global.fetch as jest.Mock).mockImplementationOnce(
      (_url: string, options: any) => new Promise((_resolve, reject) => {
        // Simulate abort by rejecting when signal is aborted
        options.signal.addEventListener('abort', () => {
          reject(mockAbortError);
        });
      })
    );

    const promise = api.generateTrendBrief(mockToken, mockTrendId);

    // Fast-forward time by 2 seconds to trigger AbortController timeout
    jest.advanceTimersByTime(2000);

    // Wait for the promise to reject with timeout error
    await expect(promise)
      .rejects
      .toThrow(new APIError(408, 'Request timeout. Please try again.'));
  });

  it('should handle generic server errors (5xx)', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(500, 'Server error. Please try again later.'));
  });

  it('should clear timeout on successful response', async () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockBriefResponse,
    });

    await api.generateTrendBrief(mockToken, mockTrendId);

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it('should clear timeout on error response', async () => {
    const clearTimeoutSpy = jest.spyOn(global, 'clearTimeout');

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 503,
    });

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(APIError);

    expect(clearTimeoutSpy).toHaveBeenCalled();
  });

  it('should handle AbortError correctly', async () => {
    // Create a real AbortController to test abort behavior
    const mockAbortError = new Error('The operation was aborted');
    mockAbortError.name = 'AbortError';

    (global.fetch as jest.Mock).mockRejectedValueOnce(mockAbortError);

    await expect(api.generateTrendBrief(mockToken, mockTrendId))
      .rejects
      .toThrow(new APIError(408, 'Request timeout. Please try again.'));
  });

  it('should preserve all BriefResponse fields', async () => {
    const fullResponse: BriefResponse = {
      ai_brief: 'Full test brief with all fields.',
      generated_at: '2026-01-13T12:34:56.789Z',
      cached: false,
    };

    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => fullResponse,
    });

    const result = await api.generateTrendBrief(mockToken, mockTrendId);

    expect(result).toHaveProperty('ai_brief');
    expect(result).toHaveProperty('generated_at');
    expect(result).toHaveProperty('cached');
    expect(result.generated_at).toBe(fullResponse.generated_at);
  });
});
